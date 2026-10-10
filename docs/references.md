# References and related work

[← Project](../README.md)

Links reviewed on 10 October 2026. These are dependencies, source materials and design reading; they do not imply endorsement or a claim to reproduce another system's results.

| Reference | How it relates |
| --- | --- |
| [Dwelly public example cases](https://github.com/DwellyOrg/HackatonPublicCases) | Source data and decision-time evaluation guidance. Our adapter preserves track/case identity and excludes future evidence. |
| [Pydantic AI](https://pydantic.dev/docs/ai/overview/) | Implemented agent runtime and structured outputs. The repository pins its actual dependency version in `uv.lock`. |
| [uv](https://docs.astral.sh/uv/) | Implemented environment and dependency workflow. |
| [Building effective agents — Anthropic](https://www.anthropic.com/engineering/building-effective-agents) | Related reading on separating workflows, agent decisions and tool interfaces. |
| [LangGraph](https://github.com/langchain-ai/langgraph) | Related work on agent orchestration; not a dependency of this project. |
| [ElevenLabs agents](https://elevenlabs.io/docs/eleven-agents/overview) | Candidate voice integration reference; provider selection remains open. |

For README organization, we looked at the [Pydantic AI](https://github.com/pydantic/pydantic-ai) and [LangGraph](https://github.com/langchain-ai/langgraph) repositories: a short product introduction, a runnable entry point and links to deeper documentation. Our architecture image is generated within this repository.

Project code is Apache 2.0. Libraries and external datasets retain their own licences and terms. A public source repository does not by itself grant permission to redistribute all its data or media.
