# TODO · Вера

Реализовать Planner в этой папке. Внешний контракт: Markdown-текст → `Plan`.

1. Создать класс с `async def plan(self, context: str) -> Plan`.
2. При создании принимать `ActionProfile`, модель и набор знаний/скиллов.
3. Использовать `profile.catalog()` как доступный словарь действий и `Plan` как схему
   ответа. Возвращать уже выбранное решение и конкретные параметры; не поручать
   исполнителю повторное рассуждение или поиск уже предоставленных данных.
4. Перед возвратом проверить `profile.validate_plan(plan)`.
5. Подключить класс вместо `HumanReviewPlanner` в `ProductionPipeline`. Тот же класс
   позже импортируется отдельным Hackathon Solver.

Готовые границы: `planning/contracts.py`, `planning/catalog.py`, `context/collector.py`,
`execution/contracts.py`. Для модели использовать существующие `BudgetedModel`,
model pool и `CaseRuntime`, как в `context/investigator.py`; не создавать отдельный
API-клиент без общего учёта и трассы. Промпты/скиллы — ресурсы пакета, не строки в CLI.

Генератор contest answer/reasoning — отдельный компонент Solver, тоже зона Веры.
На данном этапе он ещё не реализован. Текущая заглушка и её ответы — не baseline качества.
