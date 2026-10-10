# Report components

- `Report` owns six blocks: metrics, chart, records, table, flow, text. Analysis recipes own labels, units, captions and optional `note` help. Named `section` values group analysis blocks into tabs.
- Experiments: run summaries → one case index → aligned baseline/experiment columns. Answer, Evaluation, Steps and Input share the selected case and support direct links; unknown outcomes remain unknown.
- Use charts for distributions and comparisons; records for searchable evidence with drill-downs; tables for exact values; flow for ordered steps. Never encode status through colour alone.
- `theme.py`: shared palette, radius, spacing, font, Plotly defaults and `DISPLAY` precision/page size. Format numbers only for display; exports retain exact values. Recipes own units and whether a value is a percentage.
- `components.css`: shared primitives. `report.css`: workspace and report layout. `ui.js`: formatting and keyboard-accessible tabs.
- `report.js`: analysis blocks. `experiment.js`: case selection and run summaries. `case.js`: shared evidence views; nested fields open lazily, collections show eight entries at a time and long values expand on request. Labels come from saved data; full rows are interactive.
- Evaluations discover saved metric/check/flag/assessment fields. Missing values stay missing; new metrics need no renderer changes or agent reruns.
- `page.py` owns the document shell for reports, the monitor and Pages; Plotly is embedded only for charts. No frontend build, CDN or reporting server required.

- Project overview and saved experiments: `uv run --extra analysis python -m dwelly_bot.reporting.site` builds `build/pages/` from committed evidence and the installed corpus. GitHub Actions publishes it on pushes to `main`; no model credentials or paid calls. Content: `templates/site*.html`; layout: `assets/site.css`; palette remains in `theme.py`.
