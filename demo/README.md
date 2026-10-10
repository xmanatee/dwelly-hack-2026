# Show the workflow in 60 seconds

[← Project](../README.md) · [Recording storyboard](script.md) · [Submission fields](../SUBMISSION.md)

**Video status: not recorded.** Intended final path: `demo/demo.mp4`. No playable video is claimed by this page.

Show the request, the context the system actually sees, the chosen plan and an observable result. The current reproducible demonstration is a local pipeline with a placeholder Planner and mock external actions. Arithmetic executes locally.

## Two available scenes

| Scene | What viewers can inspect |
| --- | --- |
| Ticket → human review | Normalized trigger, excluded future/other-case records, the stub plan and simulated handoff/reply. |
| Calculation → ticket reply | Explicit saved fixture plan, local result `150.00`, a simulated ticket message containing that value, and durable replay. |

Use the [runnable commands](../examples/production/README.md). Label a saved fixture plan as a fixture; it is not evidence that an LLM generated the decision. When Vera's Planner is ready, replace that scene with a real captured model run and update the narration.

## Recording slots

- [ ] Record the final implemented workflow, at most about 60 seconds.
- [ ] Add the real video file inside the repository at the chosen path.
- [ ] Check playback and duration; show actual outputs without editing failed answers.
- [ ] Add voice footage only if an actual voice integration exists.
- [ ] Fill the committed video path and freeze/result commit fields in `SUBMISSION.md`.

`demo/*.mp4` and `demo/*.mov` are currently ignored to avoid accidentally committing raw recordings. Once a final file exists, explicitly include that approved deliverable, using Git LFS if needed; a future path or an external link is not the video itself. Do not add a broken “Watch demo” button before the file exists.
