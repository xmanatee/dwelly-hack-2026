"""Cached pluggable vectors, density groups, neighbors and reproducible review samples."""

from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass
from typing import Literal

from dwelly_bot.analysis.discovery_types import DiscoveryRecord
from dwelly_bot.analysis.session import AnalysisContext
from dwelly_bot.contracts import JsonRecord, ModelProfile
from dwelly_bot.providers import credentials
from dwelly_bot.storage import fingerprint, save_json


@dataclass(frozen=True)
class EmbeddingConfig:
    model: str = "openai/text-embedding-3-small"
    provider: Literal["openrouter", "openai"] = "openrouter"
    key_env: str = "OPENROUTER_API_KEY"
    price_cap_per_million: float = 1
    batch_size: int = 32


async def remote_vectors(
    ctx: AnalysisContext, records: list[DiscoveryRecord], config: EmbeddingConfig
) -> list[list[float]]:
    if not ctx.model:
        raise ValueError("Remote vectors require the shared budgeted model context")
    from openai import AsyncOpenAI

    profile = ModelProfile(
        model=config.model,
        provider=config.provider,
        key_envs=[config.key_env],
        input_price_per_million=config.price_cap_per_million,
        output_price_per_million=1,
    )
    key_value = credentials(profile)[config.key_env]
    vectors: list[list[float]] = []
    async with AsyncOpenAI(
        api_key=key_value,
        base_url="https://openrouter.ai/api/v1" if config.provider == "openrouter" else None,
        max_retries=0,
    ) as client:
        for start in range(0, len(records), config.batch_size):
            batch = records[start : start + config.batch_size]
            texts = [record.text() for record in batch]
            cache_key = fingerprint(
                {
                    "stage": "embeddings-v1",
                    "texts": texts,
                    "model": config.model,
                    "provider": config.provider,
                    "price_cap": config.price_cap_per_million,
                }
            )
            async with ctx.cache.async_locked(cache_key):
                value = ctx.cache.get(cache_key)
                hit = value is not None
                if value is None:
                    ctx.event(
                        {
                            "stage": "embeddings",
                            "key": cache_key,
                            "status": "started",
                            "record_ids": [r.id for r in batch],
                        }
                    )
                    upper = (
                        (sum(len(text.encode()) for text in texts) + 4096)
                        * config.price_cap_per_million
                        / 1_000_000
                    )
                    token, account = ctx.model.ledger.reserve_account(
                        upper,
                        config.model,
                        "analysis/embeddings",
                        {f"{config.provider}:{config.key_env}": profile.account_budget_usd},
                    )
                    try:
                        async with asyncio.timeout(90):
                            response = await client.embeddings.create(
                                model=config.model,
                                input=texts,
                                encoding_format="float",
                                extra_body={
                                    "provider": {
                                        "max_price": {"prompt": config.price_cap_per_million}
                                    }
                                }
                                if config.provider == "openrouter"
                                else None,
                            )
                        raw = response.model_dump()
                        data = sorted(raw["data"], key=lambda row: row["index"])
                        if [row["index"] for row in data] != list(range(len(texts))):
                            raise ValueError(
                                "Embedding response indices do not match the submitted batch"
                            )
                        batch_vectors = [row["embedding"] for row in data]
                        if any(
                            not row or any(not math.isfinite(n) for n in row)
                            for row in batch_vectors
                        ):
                            raise ValueError("Invalid embedding vector")
                        usage = raw.get("usage", {})
                        reported = usage.get("cost")
                        cost = (
                            float(reported)
                            if reported is not None
                            else float(usage.get("prompt_tokens", 0))
                            * config.price_cap_per_million
                            / 1_000_000
                            if usage.get("prompt_tokens")
                            else upper
                        )
                        basis = (
                            "provider_reported"
                            if reported is not None
                            else "configured_embedding_price_upper_bound"
                        )
                        ctx.model.ledger.settle(token, cost, basis, raw.get("id"))
                        value = {
                            "vectors": batch_vectors,
                            "model": raw.get("model", config.model),
                            "usage": usage,
                            "cost_usd": cost,
                            "cost_basis": basis,
                            "account": account,
                        }
                    except BaseException as error:
                        ctx.model.ledger.uncertain(token)
                        ctx.event(
                            {
                                "stage": "embeddings",
                                "key": cache_key,
                                "status": "error",
                                "error": type(error).__name__,
                            }
                        )
                        raise
                    ctx.cache.put(cache_key, value)
                vectors.extend(value["vectors"])
                step = {
                    "stage": "embeddings",
                    "key": cache_key,
                    "status": "cache_hit" if hit else "computed",
                    "new_requests": 0 if hit else 1,
                }
                ctx.steps.append(step)
                ctx.event(step)
                save_json(
                    ctx.output
                    / "embeddings"
                    / (f"{len(ctx.steps):04d}-{start:06d}-" + cache_key + ".json"),
                    {
                        "record_ids": [r.id for r in batch],
                        "cache_key": cache_key,
                        "reused": hit,
                        "model": value["model"],
                        "usage": value["usage"],
                        "original_cost_usd": value["cost_usd"],
                    },
                )
    return vectors


def semantic_groups(
    records: list[DiscoveryRecord], vectors: list[list[float]], *, min_cluster_size: int = 4
) -> JsonRecord:
    import numpy as np
    from sklearn.cluster import HDBSCAN
    from sklearn.decomposition import PCA
    from sklearn.metrics.pairwise import cosine_distances
    from sklearn.preprocessing import normalize

    if len(vectors) != len(records) or len({r.id for r in records}) != len(records):
        raise ValueError("Semantic vectors and unique record IDs must align")
    if not records:
        return {"assignments": [], "clusters": [], "pairs": []}
    x = normalize(np.asarray(vectors, dtype=float))
    distances = cosine_distances(x)
    np.fill_diagonal(distances, 0)
    if len(records) >= max(20, min_cluster_size):
        model = HDBSCAN(
            min_cluster_size=min_cluster_size, min_samples=2, metric="precomputed", copy=True
        ).fit(distances)
        labels, memberships = model.labels_, model.probabilities_
    else:
        labels, memberships = np.full(len(records), -1), np.zeros(len(records))
    coords = (
        PCA(n_components=2, random_state=0, svd_solver="randomized").fit_transform(x)
        if min(x.shape) >= 2 and np.any(np.ptp(x, axis=0) > 0)
        else np.zeros((len(records), 2))
    )
    assignments, clusters = [], []
    pairs: dict[tuple[str, ...], JsonRecord] = {}
    for index, record in enumerate(records):
        neighbors = [int(i) for i in np.argsort(distances[index]) if i != index][:3]
        assignments.append(
            {
                "id": record.id,
                "cluster": int(labels[index]),
                "membership_strength": float(memberships[index]),
                "neighbor_distance": float(np.mean(distances[index, neighbors]))
                if neighbors
                else None,
                "nearest_ids": [records[i].id for i in neighbors],
                "projection_x": float(coords[index, 0]),
                "projection_y": float(coords[index, 1]),
            }
        )
        if neighbors:
            ids = tuple(sorted((record.id, records[neighbors[0]].id)))
            pairs[ids] = {"ids": list(ids), "distance": float(distances[index, neighbors[0]])}
    for label in sorted(set(int(v) for v in labels if v >= 0)):
        indices = [i for i, v in enumerate(labels) if v == label]
        medoid = min(indices, key=lambda i: float(np.mean(distances[i, indices])))
        clusters.append(
            {
                "cluster": label,
                "count": len(indices),
                "representatives": [records[medoid].id],
                "boundary_ids": [
                    records[i].id for i in sorted(indices, key=lambda i: memberships[i])[:2]
                ],
            }
        )
    return {
        "assignments": assignments,
        "clusters": clusters,
        "pairs": sorted(pairs.values(), key=lambda p: (p["distance"], p["ids"])),
        "method": "HDBSCAN on normalized full-dimensional cosine distances; PCA is display only",
        "min_cluster_size": min_cluster_size,
    }


def lexical_vectors(records: list[DiscoveryRecord]) -> list[list[float]]:
    from sklearn.decomposition import TruncatedSVD
    from sklearn.feature_extraction.text import TfidfVectorizer

    matrix = TfidfVectorizer(max_features=8000).fit_transform([r.text() for r in records])
    components = min(64, min(matrix.shape) - 1)
    vectors = (
        TruncatedSVD(n_components=components, random_state=0).fit_transform(matrix).tolist()
        if components >= 2
        else matrix.toarray().tolist()
    )
    return [[float(value) for value in row] for row in vectors]


async def map_records(
    ctx: AnalysisContext,
    records: list[DiscoveryRecord],
    *,
    embedding: EmbeddingConfig | None = None,
    min_cluster_size: int = 4,
) -> JsonRecord:
    """Explore similarities without requiring LLM screening or procedure mining."""
    if not records or len({r.id for r in records}) != len(records):
        raise ValueError("Mapping requires nonempty, uniquely identified records")
    if any(not r.text().strip() for r in records):
        raise ValueError("Remove empty analysis texts explicitly before mapping")
    vectors = (
        await remote_vectors(ctx, records, embedding)
        if embedding
        else ctx.cached(
            "lexical-vectors", [r.text() for r in records], lambda: lexical_vectors(records)
        )
    )
    geometry: JsonRecord = ctx.cached(
        "density-discovery",
        {
            "ids": [r.id for r in records],
            "vectors_hash": fingerprint(vectors),
            "min_cluster_size": min_cluster_size,
        },
        lambda: semantic_groups(records, vectors, min_cluster_size=min_cluster_size),
    )
    geometry["embedding_model"] = embedding.model if embedding else "TF-IDF/SVD lexical baseline"
    save_json(ctx.output / "cluster_summary.json", geometry)
    return geometry
