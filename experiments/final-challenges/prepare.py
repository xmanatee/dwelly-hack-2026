"""Project released challenge evidence into Winner inputs without changing originals."""

import argparse
import shutil
import subprocess
from pathlib import Path

from dwelly_bot.storage import file_hash, save_json

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("source", type=Path)
parser.add_argument("output", type=Path)
args = parser.parse_args()
if args.output.exists():
    raise SystemExit("Prepared input already exists; preserve it and choose a fresh directory")
shutil.copytree(args.source, args.output)
inventory = {}
for case in sorted(args.source.iterdir()):
    if not case.is_dir():
        continue
    # Development indexes are retrospective; released challenge indexes are live requests.
    shutil.copyfile(case / "index.md", args.output / case.name / "request.md")
    for original in sorted(case.rglob("*")):
        if not original.is_file():
            continue
        relative = original.relative_to(args.source).as_posix()
        inventory[relative] = file_hash(original)
        if original.suffix.lower() in {".png", ".jpg", ".jpeg"}:
            text = subprocess.run(
                ["tesseract", str(original), "stdout"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            if not text.strip():
                raise ValueError(f"No image text extracted: {relative}")
            target = args.output / relative
            target.with_suffix(target.suffix + ".ocr.txt").write_text(
                f"# Local OCR of {original.name}\n\n"
                "Machine transcription; the original image is preserved.\n\n" + text
            )
save_json(args.output.parent / "input-manifest.json", inventory)
print(f"Prepared {len(list(args.output.glob('*/history.md')))} cases")
