"""CLI: python -m synth.build --out out --seed 7 --per-variant 3"""

from __future__ import annotations

import argparse
import collections
import importlib
import json
import pkgutil
import random
import sys
from pathlib import Path

from . import pools, scenarios
from .core import REGISTRY, CaseBuilder, World, case_seed
from .export import write_all


def load_scenarios():
    for m in pkgutil.iter_modules(scenarios.__path__):
        importlib.import_module(f"{scenarios.__name__}.{m.name}")


def pick_bank(rng: random.Random, home_only: bool) -> dict:
    banks = pools.HOME_BANKS[:1] if home_only else pools.HOME_BANKS
    b = rng.choices(banks, [w for *_, w in banks])[0]
    return dict(bank_id=b[0], name=b[1], short=b[2], sort_code_prefix=b[3])


def build(seed: int, per_variant: int, only: list[str] | None, home_only: bool) -> World:
    load_scenarios()
    world = World(seed)
    n = 0
    failures = []
    for name in sorted(REGISTRY):
        sdef = REGISTRY[name]
        if only and name not in only and sdef.family not in only:
            continue
        for variant in sdef.variants:
            for i in range(per_variant * sdef.weight):
                rng = random.Random(case_seed(seed, name, variant, i))
                n += 1
                b = CaseBuilder(world, sdef, variant, n, rng, pick_bank(rng, home_only))
                try:
                    sdef.fn(b, variant)
                    b.check()
                except Exception as exc:  # report every broken scenario, not just the first
                    failures.append(f"{name}/{variant}#{i}: {type(exc).__name__}: {exc}")
                    n -= 1
                    continue
                world.cases.append(b)
    if failures:
        print("\n".join(failures), file=sys.stderr)
        raise SystemExit(f"{len(failures)} case(s) failed to build")
    return world


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="out")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--per-variant", type=int, default=3, help="cases per scenario variant (x scenario weight)")
    ap.add_argument("--only", nargs="*", help="scenario names or families to build")
    ap.add_argument("--home-only", action="store_true", help="only Harrow & Vale as the home bank")
    a = ap.parse_args(argv)
    world = build(a.seed, a.per_variant, a.only, a.home_only)
    out = Path(a.out)
    write_all(world, out)
    stats = dict(
        cases=len(world.cases),
        scenarios=len({b.sdef.name for b in world.cases}),
        variants=len({(b.sdef.name, b.variant) for b in world.cases}),
        by_family=dict(collections.Counter(b.sdef.family for b in world.cases)),
        by_difficulty=dict(collections.Counter(b.difficulty for b in world.cases)),
        by_path=dict(collections.Counter(b.labels["expected_path"] for b in world.cases)),
        by_bank=dict(collections.Counter(b.bank["short"] for b in world.cases)),
        attachments=sum(len(b.attachments) for b in world.cases),
        record_rows={t: len(r) for t, r in sorted(world.rows.items())},
    )
    (out / "stats.json").write_text(json.dumps(stats, indent=2))
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
