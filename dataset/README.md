# Banking public-case contract

Source: [Dwelly public examples](https://github.com/DwellyOrg/HackatonPublicCases), commit `9bcdca585955dfb930005ed742572606e68f5688`.

The [organizer README](https://github.com/DwellyOrg/HackatonPublicCases/blob/9bcdca585955dfb930005ed742572606e68f5688/README.md) describes **completed synthetic examples for development**, not a ready-made next-action benchmark or a bank API. There are 200 cases across four tracks; this project selects all 50 banking cases. Public case identity is **source population + track + organizer number**. `banking-041` preserves banking case `041`; neither another track's `041` nor a challenge case `041` is the same case.

## Read the cases, then define a test

1. For development study, begin with the original `index.md`, then read the complete `history.md` and attachments. Index sections vary in the general format. Summaries, completed status and outcomes are public retrospective material, not secret evaluator labels.
2. For a next-decision test, choose an explicit event cutoff. Include the initial request, events through that cutoff and attachments demonstrably available then. Exclude later events and ending-revealing titles, summary/outcome fields and completion metadata.
3. Capture the agent's actual answer, evidence reads and proposed actions. Compare that saved decision with the later public evidence **after execution**, considering what was knowable at the cutoff and acceptable alternatives. A recorded outcome is an example, not a unique correct answer. Our mechanical citation checks do not perform this semantic review.
4. Keep unseen challenge cases separate. Public example results must not be submitted. The organizer names the submission population `HackatonChallendges/`; its spelling is intentional here. Its released input contract must be inspected before adding a challenge adapter.

Full public-case study and decision-time execution are different views of the same sources. Never put retrospective review output in an agent evidence directory, inject later evidence through retrieval, or pretend that replaying a later historical message is a live tool response.

## Reproduce the historical baseline

`uv run python dataset/fetch.py` installs the historical **v1** view in `dataset/`: exactly two events per case, with every attachment excluded. This is a local experiment choice, not an organizer rule. It is retained to reproduce the saved baseline, including its missing early attachment in case 041. An existing installation is never silently rewritten.

## Build a reviewed snapshot

```sh
# Reuse the original ZIP; writes a separate ignored corpus and makes no model calls.
uv run python dataset/fetch.py --archive dataset/release.zip \
  --profile configs/banking-development.json --root .cache/datasets/banking-reviewed

# Explicitly select the corrected corpus when executing or analyzing it.
uv run dwelly-bot run dwelly-banking \
  --dataset-root .cache/datasets/banking-reviewed \
  --config experiments/banking-data-contract/config.json --experiment banking-data-contract
```

The second command is paid execution; it has **not** been run as part of the data-contract audit. Omitting `--dataset-root` uses the historical `dataset/` corpus. Snapshot changes require a new control round; they cannot be presented as a same-input improvement over the v1 baseline.

[The reviewed profile](../configs/banking-development.json) selects a default cutoff and optional per-case `after_event` overrides. Every attachment has a reviewed availability event and an explanation. The installer checks that the original exists and that the cited event identifies it; this is a structural check, not an automated proof that a mention grants access. Update the review when changing the source or agent role. Attachment dates, reporting periods, filenames and filesystem times do not establish availability.

| Case | Original attachment | Conservative availability event | At the default cutoff, event 002 |
| --- | --- | --- | --- |
| 031 | statement-031.pdf | 004 | Withheld |
| 032 | statement-032.pdf | 006 | Withheld |
| 033 | transactions-033.csv | 005 | Withheld |
| 038 | account-confirmation-038.pdf | 004 | Withheld |
| 039 | sessions-039.txt | 006 | Withheld |
| 040 | payment-record-040.pdf | 005 | Withheld |
| 041 | batch-041.csv | 001 | Available: customer-uploaded input; bank receipt is still unconfirmed |
| 042 | validation-042.txt | 004 | Withheld |
| 049 | merchant-report-049.csv | 005 | Withheld |

The pinned banking corpus has 258 history events and nine attachments (three CSVs, two text files, four PDFs). All nine attachments and their availability evidence were inspected in the data-contract audit. The corrected default view contains 100 history events and one attachment. Event 002 is not always the same workflow stage: case 032 already records an archive request, while case 039 still precedes the customer's secure-portal confirmation.

CSV, TXT and Markdown attachments are rendered as separate line-addressable Markdown documents, preserving their original text and source filename. Original bytes remain unchanged. Selecting an available PDF or image currently fails explicitly until a media reader is implemented; do not silently omit it or manipulate the cutoff to conceal that limitation.

## Files and enforcement

Archive SHA256: `509c75fc1e50960165c4323b0fe74ae265f882e3e3b4c8d59ea2f58613a926b9`. The installer verifies the archive, retains it unchanged as `release.zip`, extracts original banking bytes to `original/Banking & Financial Services/`, and pins every installed data file in `source.json`. A verified reinstall is a no-op; modified or unowned files cause an error. Use `--root` with a new empty directory to validate a clean install.

`cases.json` preserves track, organizer number, split, cutoff and source URLs. Version 2 also records the decision profile and exact visible document inventory. `source.json` pins the originals, derived views and full profile for offline inspection. Only `documents/banking-NNN/` is exposed to the agent. The adapter validates the development identity, allowed documents, contiguous event prefix and cutoff timestamp. It cannot ingest challenge cases by changing a split label.

The runtime has read-only documents and arithmetic. Proposed referrals, checks and messages are not executed actions. Later histories and the attachment availability profile are never supplied as tool responses. [Analysis usage](../analysis/README.md) explains visible-only exploration and explicit retrospective review with saved answers.

Corpus and original archives stay ignored. No secret or dataset bytes belong in Git. The installer and documentation are source.
