"""Offline, evaluation-specific review. Never imported by runtime retrieval or source analytics."""

# ruff: noqa: RUF001 -- The report deliberately uses Russian prose.

from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from dwelly_bot.analysis import AnalysisContext, Report
from dwelly_bot.storage import file_hash, load_json, save_json

CORE = ("plan_action", "answer_action", "generator_fidelity", "grounding", "safety_scope")


def build(ctx: AnalysisContext) -> Report:
    """Read one pinned public evaluation, preserving every raw judgment and failed case."""
    source_files = [ctx.data / name for name in ("results.json.gz", "captures.json.gz")]
    ctx.sources.update({p.name: file_hash(p) for p in source_files})
    bundle = load_json(source_files[0])
    captures = load_json(source_files[1])["files"]
    review_path = Path(__file__).with_name("review.json")
    review = load_json(review_path)
    ctx.parameters["review_sha256"] = file_hash(review_path)
    rows = bundle["cases"]
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate decision IDs")
    annotations: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for finding in review["findings"]:
        for cid in finding["cases"]:
            if cid not in ids:
                raise ValueError(f"Unknown reviewed decision {cid}")
            annotations[cid].append(finding)

    grades: dict[str, Counter[str]] = defaultdict(Counter)
    selection_sizes: Counter[int] = Counter()
    selections: Counter[str] = Counter()
    repair_counts: Counter[str] = Counter()
    repair_cases: dict[str, set[str]] = defaultdict(set)
    first = {
        scenario: min(r["id"] for r in rows if r["scenario"] == scenario)
        for scenario in {r["scenario"] for r in rows}
    }
    stages: dict[str, Counter[str]] = defaultdict(Counter)
    plans = completed = core_pass = 0
    records: list[dict[str, Any]] = []
    case_metrics: list[dict[str, Any]] = []
    for row in rows:
        cid = row["id"]
        context = captures[f"prepared/inputs/{cid}/context.md"]
        # The grader's input must be the same bounded context used by Winner.
        winner_context = f"# Supplied case {cid}\n\n## context.md\n\n{context}"
        if row["input"] != context or captures[f"winner/{cid}/context.md"].rstrip(
            "\n"
        ) != winner_context.rstrip("\n"):
            raise ValueError(f"Context mismatch for {cid}")
        journal = [
            json.loads(line) for line in captures[f"winner/journals/{cid}.jsonl"].splitlines()
        ]
        skill_records = [
            j
            for j in journal
            if j.get("tool") == "select_planner_skills" and j.get("status") == "returned"
        ]
        if len(skill_records) != 1:
            raise ValueError(f"Expected one recorded selection for {cid}")
        selected = skill_records[0]["result"]["selected"]
        selection_sizes[len(selected)] += 1
        selections.update(selected)
        repairs: Counter[str] = Counter()
        for record in journal:
            for role in record.get("roles", []):
                for message in role["messages"]:
                    for part in message.get("parts", []):
                        if part.get("part_kind") != "retry-prompt":
                            continue
                        body = str(part.get("content", ""))
                        kind = (
                            "evidence_ids"
                            if "unknown evidence" in body
                            else "completion_wording"
                            if "planned action as done" in body
                            else "schema"
                            if "list_type" in body
                            else "other"
                        )
                        repairs[kind] += 1
                        repair_cases[kind].add(cid)
        repair_counts.update(repairs)
        verdicts = {j["criterion"]: j["status"] for j in row["judge"]}
        for criterion, status in verdicts.items():
            grades[criterion][status] += 1
        stages["first" if cid == first[row["scenario"]] else "later"][verdicts["plan_action"]] += 1
        plan = next((s["plan"] for s in row["sources"] if s.get("plan")), None)
        plans += bool(plan and plan.get("steps"))
        completed += row["execution_status"] == "success"
        core_pass += all(verdicts[c] == "pass" for c in CORE)
        case_metrics.append(
            {
                "id": cid,
                "scenario": row["scenario"],
                "selected_skills": selected,
                "repairs": dict(repairs),
                "verdicts": verdicts,
                "findings": [f["id"] for f in annotations[cid]],
            }
        )
        records.append(
            {
                "id": cid,
                "title": cid,
                "summary": "; ".join(f["id"] for f in annotations[cid]) or row["judge_summary"],
                "fields": {
                    "Plan judgment": verdicts["plan_action"],
                    "Skills": ", ".join(selected),
                    "Execution": row["execution_status"],
                    "Repairs": dict(repairs),
                },
                "sources": [
                    {
                        "id": "context",
                        "source": f"prepared/inputs/{cid}/context.md",
                        "text": context,
                    },
                    {
                        "id": "reference",
                        "source": "Withheld public next event; NOT unique gold or runtime evidence",
                        "text": row["reference"]["action"],
                    },
                    {
                        "id": "plan",
                        "source": "Saved structured plan",
                        "text": json.dumps(plan, ensure_ascii=False, indent=2),
                    },
                    {"id": "answer", "source": "Saved ANSWER", "text": row["answer"]},
                    {
                        "id": "reasoning",
                        "source": "Saved public rationale",
                        "text": row["public_rationale"],
                    },
                    {
                        "id": "judge",
                        "source": "Unmodified saved judge",
                        "text": json.dumps(row["judge"], ensure_ascii=False, indent=2),
                    },
                    {
                        "id": "review",
                        "source": "Manual interpretation, not a replacement grade",
                        "text": json.dumps(annotations[cid], ensure_ascii=False, indent=2),
                    },
                    {
                        "id": "error",
                        "source": "Saved execution error",
                        "text": str(row["error"] or "None"),
                    },
                ],
            }
        )

    ordinary = random.Random(review["ordinary_sample_seed"]).sample(
        [r["id"] for r in rows if all(j["status"] == "pass" for j in r["judge"])], 8
    )
    nonpass = [r["id"] for r in rows if any(j["status"] != "pass" for j in r["judge"])]
    findings = {
        "sources": {p.name: file_hash(p) for p in source_files},
        "review_sha256": file_hash(review_path),
        "decisions": len(rows),
        "scenarios": len(first),
        "valid_plans": plans,
        "completed_outputs": completed,
        "core_pass": core_pass,
        "grades": {k: dict(v) for k, v in grades.items()},
        "skill_counts": dict(selections),
        "selected_skill_count_distribution": dict(selection_sizes),
        "stage_plan_judgments": {k: dict(v) for k, v in stages.items()},
        "repair_counts": dict(repair_counts),
        "repair_cases": {k: sorted(v) for k, v in repair_cases.items()},
        "review_inventory": {
            "all_nonpass": nonpass,
            "ordinary_sample": ordinary,
            "seed": review["ordinary_sample_seed"],
            "targeted": sorted(cid for cid, notes in annotations.items() if notes),
        },
        "case_metrics": case_metrics,
        "manual_review": review,
        "new_model_requests": 0,
        "new_model_cost_usd": 0,
    }
    save_json(ctx.output / "findings.json", findings)
    report = Report(
        title="Planner: решения, ограничения и ошибки оценки",
        subtitle="102 решения из 50 публичных сценариев · сохранённый Sonnet → Opus · без новых модельных вызовов",
    )
    report.receipt = {
        "source_hashes": findings["sources"],
        "review_sha256": file_hash(review_path),
        "new_model_requests": 0,
        "retrospective_evaluation_review": True,
    }
    report.metrics(
        {
            "Decisions": len(rows),
            "Scenarios": len(first),
            "Valid plans": plans,
            "Complete outputs": completed,
            "All 5 core criteria pass": core_pass,
            "Evidence repair cases": len(repair_cases["evidence_ids"]),
        }
    )
    report.text(
        "Главный вывод",
        "Проблема не в числе загруженных скиллов: 77/102 решений получили один, максимум — три. Основной дефект — выбор следующего действия при нехватке банковского факта. Planner умеет пересказать готовый статус, но иногда вместо конкретной внутренней проверки просит данные у клиента или завершает кейс. Есть и чрезмерные процедуры в одобренных джаджем планах. Нужны правила применимости и учёт стадии процесса, а не ещё один большой слой запретов.",
        collapsed=False,
    )
    report.table(
        "Оценки джаджа — без ручного исправления",
        [
            {"criterion": c, **{s: v.get(s, 0) for s in ("pass", "fail", "unknown")}}
            for c, v in grades.items()
        ],
        note="Единица — решение. 102 решения внутри 50 сценариев зависимы; это development-набор, не holdout.",
    )
    report.table(
        "Реально выбранные скиллы",
        [{"skill": k, "decisions": v} for k, v in selections.most_common()],
        note="vulnerability-support, bereavement-authority, crisis-support и financial-abuse не выбирались. Общие safety-инструкции всё равно загружались. Отсутствие этих тем в выборке не основание удалять их поддержку.",
    )
    report.table(
        "Стадия процедуры",
        [{"stage": k, **dict(v)} for k, v in stages.items()],
        note="First — самый ранний выбранный срез каждого сценария. Это корреляция: поздние срезы чаще уже содержат готовый банковский результат.",
    )
    report.table(
        "Ручной разбор: наблюдения и предложения",
        [
            {
                "finding": f["id"],
                "confidence": f["confidence"],
                "cases": ", ".join(f["cases"]),
                "observation": f["observation"],
                "proposal": f["proposal"],
            }
            for f in review["findings"]
        ],
    )
    report.table(
        "Технические повторы",
        [
            {"kind": k, "retry_prompts": v, "distinct_cases": len(repair_cases[k])}
            for k, v in repair_counts.items()
        ],
        note="87 исправлений ссылок не означают 87 плохих банковских решений. Prepared context.md — один документ; event 001 в его тексте не зарегистрирован как отдельный evidence ID.",
    )
    report.flow(
        "Предлагаемое правило выбора следующего действия",
        [
            {
                "title": "Факт уже дан",
                "condition": "Ответить по нему; не запускать завершённую процедуру заново.",
            },
            {
                "title": "Факт принадлежит банку",
                "condition": "Запланировать конкретную проверку записи или обращение к ответственной команде.",
            },
            {
                "title": "Нужны намерение или согласие",
                "condition": "Задать минимальный вопрос клиенту; не угадывать согласие.",
            },
            {
                "title": "Есть риск или ограничение полномочий",
                "condition": "Применить подходящий gate; внутреннее чтение, раскрытие и изменение — разные действия.",
            },
        ],
        note="Это альтернативы по контексту, не четыре обязательных шага. Пока предложение, не изменение runtime.",
    )
    report.text(
        "Метод и ограничения",
        f"Просмотрены все 102 краткие записи, все {len(nonpass)} случая с хотя бы одной оценкой не pass, целевые подозрительные pass и 8 случайных обычных примеров (seed {review['ordinary_sample_seed']}): {', '.join(ordinary)}. Эти восемь примеров подтверждают сильную сторону — осторожный ответ по готовой банковской записи. Ручные выводы не являются независимой новой экспертной разметкой. Историческое следующее событие иногда вводит новые факты и не является уникальным правильным ответом. Модели решения и судьи относятся к одному поставщику. Банковские действия не исполнялись. Новые запросы/расход: 0. Сохранённые оценки и runtime не изменены.",
        collapsed=False,
    )
    report.records(
        "Все решения: контекст → план → ответ → судья → разбор",
        records,
        note="Reference показывается только для ретроспективного анализа; он не был доступен Planner.",
    )
    return report
