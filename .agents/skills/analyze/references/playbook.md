# Text and operational data playbook

Select branches by question. Built-in functions below are tools; the alternatives are research directions, not installed dependencies or required stages.

## Choose the unit and preserve meaning

- Profile source roles, languages, lengths, date range, missing/duplicate IDs and joins. Use `analysis.data.Table`, `relationships`, `enrich`, `threads`; `analysis.recipes.profile`, `segments`, `numeric_summary`, `sample`, `exceptions`.
- Keep `raw_text` and derived analysis text separately, linked by stable source ID. Remove repeated signatures/quoted email history only when appropriate; retain negation, amounts, dates, authors and chronology. Inspect what cleaning removed. Don't count the same quoted request in every reply.
- Split long documents by meaningful sections with parent IDs and offsets. Embedding/truncation limits depend on the selected model; never silently cut off the relevant end. Aggregate to parent case/thread before reporting case counts. Analyze requests, policies and evidence documents separately before relating them.
- Duplicates, shared customers/cases and time leakage can contaminate later evaluations. Hold out by the relevant entity/time unit, not randomly by near-identical text. Use only public/source fields; evaluation labels are not exploration input.

## What topics recur?

- Start with `text_records` → `semantic.map_records` → `topics.add_topics` for a reusable cached vector map, HDBSCAN groups, neighbors, representatives and boundary cases. `add_topics` also renders the map and review lists. Pass `EmbeddingConfig` for OpenRouter/OpenAI vectors, or explicitly choose lexical TF-IDF/SVD; small-corpus HDBSCAN currently leaves fewer than 20 records unassigned. The pairwise distance matrix is quadratic: estimate memory before scaling beyond a few thousand records.
- Keyword hints summarize groups; they are not names from an LLM. Read medoids and boundaries before naming groups. For mixed-intent threads, consider request-level segmentation or multiple topic labels rather than forcing one label per thread.
- If groups reflect templates, language or document length, adjust the unit/cleaning/model and compare the same examples. If density groups are unstable or mostly unassigned, try different `min_cluster_size`, lexical `recipes.text_groups` (KMeans), or a small reviewed taxonomy. Do not force every point into a topic or tune only for a pretty plot.
- Compare a small number of plausible settings on cached vectors: assigned fraction, group sizes, member overlap, representative agreement and random-source review. Silhouette is a geometry diagnostic, not semantic correctness. Stop when the result supports a useful decision.
- [BERTopic practices](https://maartengr.github.io/BERTopic/getting_started/best_practices/best_practices.html): reusable embeddings, tunable clustering and topic representation. [scikit-learn text clustering](https://scikit-learn.org/stable/auto_examples/text/plot_document_clustering.html): a compact lexical baseline and evaluation examples.

## Duplicates, anomalies and typos

- Exact normalized-text hashes find repeats; embedding neighbors propose near-duplicates. Compare differing IDs, amounts, dates and negation before merging. Repeated templates are not necessarily repeated cases. Keep original members and frequency counts.
- Review both HDBSCAN-unassigned points and high neighbor-distance points, plus a random comparison sample. Rare topic, operational severity and malformed data are separate findings; an unusual name or spelling is not vulnerability/fraud evidence.
- Use character n-grams/edit distance for suspected spelling variants in controlled categories/entity names; verify against IDs and source context. Do not autocorrect raw customer text or merge people by fuzzy name alone.
- [Sentence Transformers paraphrase mining](https://sbert.net/examples/sentence_transformer/applications/paraphrase-mining/) offers chunked similarity search for larger corpora. [UMAP guidance](https://umap-learn.readthedocs.io/en/latest/clustering.html) explains clustering tradeoffs; two-dimensional separation does not establish topic quality.

## Which records need operational attention?

- After topics help organize the workload, consider targeted cited extraction: required facts, missing evidence, conflicting accounts, stated support needs, deadlines or ambiguity. Start with `analysis.llm.extract` and `AnalysisContext.ask`; use `discover` only when its multiple screening/taxonomy/audit stages answer the question.
- Inspect flagged examples and randomly selected unflagged examples. A model's second review reveals disagreement, not precision/recall without reviewed labels. Track failed, excluded and unscreened rows in the denominator.
- Compare same-entity facts with source/date/authority before calling disagreement a contradiction. Pairwise text similarity alone does not prove the facts concern the same event. Distinguish policy instructions, observed messages, hypothetical scenarios and agent-generated claims.
- Procedure mining requires actual multi-case handling histories. Use `threads` and the discovery pattern/draft stages if available; document/question corpora only support proposed procedures, not claims about observed resolution paths. Human review precedes runtime adoption.

## Segments, time and measured performance

- Cross topics with reliable channel, product, date, lifecycle stage or customer attributes: use `segments`, `charts.matrix`, `composition`, `ranking` and `histogram`. Show denominators and missing metadata; avoid demographic inference from writing style.
- Timelines/response times need genuine timestamps and event definitions. Count reopened/unresolved cases separately; absence of a reply does not prove resolution. No causality claim from a segment correlation.
- Saved-run overlays can identify failure concentration by topic/length/evidence gap, but must use the same pinned dataset. Keep source analysis distinct from agent performance and evaluator outputs. Suggest evaluation cases from observed gaps; do not manufacture correct answers.

## Reviewable output and continuation

- Start with findings and coverage; then group sizes, clickable source map, examples/boundaries and an outlier queue. Shared `Report` blocks and `add_semantic_map` already support click-to-inspect. Use Plotly legend controls to isolate groups; use source IDs to connect selections and review notes.
- PCA/UMAP are navigation aids. Prefer lists or cross-tabs when the projection hides the distinction; don't build a dashboard just to show every file. Use common numeric precision/colors, concise captions and collapsed method details.
- Keep a reproducible Python recipe under `analysis/`, outputs under `analysis/artifacts/`, caches under `.cache/analysis/`. `AnalysisContext.cached` records source/code hashes; `remote_vectors` caches ordered text batches by model/provider/text, so keep batches stable for reuse. Presentation changes use saved report rendering. Persist chosen parameters, exclusions, sampling seed and reviewer corrections; don't create a new general configuration framework.
- [OpenRouter embeddings](https://openrouter.ai/docs/api/api-reference/embeddings/submit-an-embedding-request) and [model inventory](https://openrouter.ai/docs/api/api-reference/embeddings/list-embeddings-models): verify supported model, limits and pricing before paid work; cheap embeddings don't imply cheap full-corpus LLM screening.
- Skill examples to consult, not auto-install: [K-Dense EDA](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/exploratory-data-analysis/SKILL.md) for explicit observation units and limitations; [DalyKit](https://github.com/taehyunan-99/DalyKit) for analysis workflows. Our unit of reuse is a small Python recipe, with HTML or a notebook chosen for the task.
