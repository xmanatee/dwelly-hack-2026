# Banking development data

Source: [Dwelly public examples](https://github.com/DwellyOrg/HackatonPublicCases), commit `9bcdca585955dfb930005ed742572606e68f5688`.

```sh
uv run python dataset/fetch.py
# Reproduce without downloading, using the exact original archive:
uv run python dataset/fetch.py --archive /absolute/path/release.zip
```

Archive SHA256: `509c75fc1e50960165c4323b0fe74ae265f882e3e3b4c8d59ea2f58613a926b9`. The installer verifies the archive, retains it unchanged as `release.zip`, extracts original banking bytes to `original/Banking & Financial Services/`, and pins every installed data file in `source.json`. A verified reinstall is a no-op; modified or unowned files cause an error. Use `--root` with a new empty directory to validate a clean install.

All 50 cases are development examples. `cases.json` preserves track, organizer number and source URLs. `documents/banking-NNN/` contains only the initial request and history through event 002. Titles and completed status, overview, suggested next action, outcomes and later events are not passed to the agent or analysis. All attachments are withheld because availability at the cutoff has not been verified. Never broaden the evidence directory to `original/`.

The [organizer README](https://github.com/DwellyOrg/HackatonPublicCases/blob/9bcdca585955dfb930005ed742572606e68f5688/README.md) says completed outcomes are examples, not unique correct answers; it requires withholding future information when testing the next decision. No outcome labels are fabricated here. Cases in `HackatonChallendges/` are a separate submission population even when numbers match. They have not been fetched or used.

Corpus and original archives stay ignored. No secret or dataset bytes belong in Git. The installer and documentation are source.
