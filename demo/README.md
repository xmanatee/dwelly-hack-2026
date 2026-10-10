# Product and voice demos

[← Project](../README.md) · [Submission metadata](../SUBMISSION.md)

[![Watch the main product demo](dashboard-preview.jpg)](dashboard.mp4)

| Recording | What it shows | Duration |
| --- | --- | --- |
| **[Main demo — case desk](dashboard.mp4)** | Banking cases, decisions, operator queue and quality review. Dashboard figures show earlier development runs, not the final challenge score. | 65.87 s |
| **[Voice call](voice-call.mp4)** | ElevenLabs conversation connected to the Dwelly call pipeline. | 46.60 s |

Both MP4 files are committed directly in this repository, with H.264 video and AAC audio.
The main recording is slightly longer than the guide's approximately 60-second target;
the uploaded recording is preserved unchanged.

The voice bridge returns the case pipeline's reply to the caller within the same conversation.
The reproducible demo uses a prepared fixture plan. Live speech does not imply a live bank
transaction: handoffs and external banking effects remain simulated.
[Voice setup and limits](../examples/voice/README.md).

[Final challenge answers](../ANSWERS/README.md) are separate from the dashboard's historical
results. They retain the actual generated outputs, plans and traces for all 30 banking cases.
