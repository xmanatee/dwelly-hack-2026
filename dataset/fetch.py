"""Install pinned original Dwelly bytes and isolated banking development views."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlopen

from dwelly_bot.adapters.banking import TRACK, initial_view
from dwelly_bot.adapters.banking_data import DecisionProfile, visible_attachments
from dwelly_bot.data import pin
from dwelly_bot.experiments.provenance import dataset_hash

COMMIT = "9bcdca585955dfb930005ed742572606e68f5688"
SHA256 = "509c75fc1e50960165c4323b0fe74ae265f882e3e3b4c8d59ea2f58613a926b9"
REPOSITORY = "https://github.com/DwellyOrg/HackatonPublicCases"
URL = f"https://codeload.github.com/DwellyOrg/HackatonPublicCases/zip/{COMMIT}"


def install(
    root: Path, archive: Path | None = None, profile: DecisionProfile | None = None
) -> None:
    # No profile reproduces the immutable historical v1 corpus, including its limits.
    version = 2 if profile else 1
    root.mkdir(parents=True, exist_ok=True)
    if (root / "source.json").exists():
        dataset_hash(root)  # Refuse any modified or added data; never silently replace it.
        receipt = json.loads((root / "source.json").read_text())
        if (
            receipt.get("release_commit") != COMMIT
            or receipt.get("view_version") != version
            or receipt.get("decision_profile") != (profile.model_dump() if profile else None)
        ):
            raise ValueError("Installed release/profile differs; choose a new empty data directory")
        print("Pinned banking development dataset already installed and verified")
        return
    unexpected = {p.name for p in root.iterdir()} - {"README.md", "fetch.py"}
    if unexpected:
        raise ValueError(f"Destination contains unowned data: {sorted(unexpected)}")
    payload = archive.read_bytes() if archive else urlopen(URL, timeout=60).read()
    if hashlib.sha256(payload).hexdigest() != SHA256:
        raise ValueError("Release archive SHA256 mismatch")
    with tempfile.TemporaryDirectory(prefix="dwelly-install-", dir=root.parent) as scratch:
        stage = Path(scratch)
        (stage / "release.zip").write_bytes(payload)
        with zipfile.ZipFile(io.BytesIO(payload)) as zipped:
            prefix = f"HackatonPublicCases-{COMMIT}/"
            for info in zipped.infolist():
                if info.is_dir() or not info.filename.startswith(prefix):
                    continue
                relative = info.filename.removeprefix(prefix)
                if relative != "README.md" and not relative.startswith(TRACK + "/"):
                    continue
                path = stage / "original" / relative
                if not path.resolve().is_relative_to((stage / "original").resolve()):
                    raise ValueError("Archive path escapes its root")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(zipped.read(info))
        cases = []
        if profile:
            profile.validate_cases({p.name for p in (stage / "original" / TRACK).iterdir()})
        for folder in sorted((stage / "original" / TRACK).iterdir()):
            number = folder.name
            if not folder.is_dir() or not number.isdecimal():
                raise ValueError("Unexpected case directory")
            after_event = (
                profile.after_event.get(number, profile.default_after_event) if profile else 2
            )
            full_history = (folder / "history.md").read_text()
            request, history, decision_time = initial_view(
                (folder / "index.md").read_text(), full_history, events=after_event
            )
            identifier = f"banking-{number}"
            visible = stage / "documents" / identifier
            visible.mkdir(parents=True)
            (visible / "request.md").write_text("# Initial request\n\n" + request + "\n")
            (visible / "history.md").write_text(history)
            attachments = (
                visible_attachments(
                    folder, full_history, after_event, profile.attachments.get(number, [])
                )
                if profile
                else {}
            )
            for name, content in attachments.items():
                path = visible / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            sources = [
                f"{REPOSITORY}/blob/{COMMIT}/Banking%20%26%20Financial%20Services/{number}/{name}.md"
                for name in ("index", "history")
            ]
            cases.append(
                {
                    "id": identifier,
                    "organizer_id": number,
                    "track": TRACK,
                    "split": "development",
                    "request": request,
                    "decision_time": decision_time,
                    "visible_events": after_event,
                    "sources": sources,
                }
            )
            if profile:
                cases[-1].update(
                    view_version=2,
                    decision_profile=profile.name,
                    evidence_documents=["request.md", "history.md", *sorted(attachments)],
                )
        if [row["organizer_id"] for row in cases] != [f"{n:03}" for n in range(1, 51)]:
            raise ValueError("Expected all 50 released Banking development cases")
        (stage / "cases.json").write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n")
        pin(stage)
        receipt = json.loads((stage / "source.json").read_text())
        receipt.update(
            origin=REPOSITORY,
            release_commit=COMMIT,
            archive_sha256=SHA256,
            track=TRACK,
            split="development",
            view_version=version,
            decision_point=(
                "Explicit event cutoffs and reviewed attachment availability; later evidence withheld"
                if profile
                else "After event 002; later history, summaries and all attachments withheld"
            ),
        )
        if profile:
            receipt["decision_profile"] = profile.model_dump()
        (stage / "source.json").write_text(json.dumps(receipt, indent=2) + "\n")
        dataset_hash(stage)
        for entry in stage.iterdir():
            entry.rename(root / entry.name)
    print(f"Installed {len(cases)} banking development cases at {root}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="Local copy of the pinned original ZIP")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument(
        "--profile",
        type=Path,
        help="Reviewed decision/attachment profile; omit only to reproduce the historical v1 corpus",
    )
    args = parser.parse_args()
    profile = (
        DecisionProfile.model_validate_json(args.profile.read_text()) if args.profile else None
    )
    install(args.root, args.archive, profile)


if __name__ == "__main__":
    main()
