"""Put the app on a Hugging Face Space (Docker, free CPU).

    hf auth login                                         # once, with a write token from huggingface.co
    python scripts/deploy_space.py                        # dry run: lists what would go up
    python scripts/deploy_space.py --upload               # creates the Space if needed and uploads
    python scripts/deploy_space.py --space you/name --upload

Only files tracked by git go up, plus the demo images in demo_cache/ (not in git), so nothing private in the
folder can leak. The Space's README is docs/SPACE_CARD.md (its settings block and a short intro).
The Meta key is never uploaded: add MODEL_API_KEY (and FIRMS_MAP_KEY) as secrets in the Space settings.
Needs only the standard library and huggingface_hub.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPACE_NAME = "what-changed-here"
NEVER = (".env", ".pdf", ".key")   # a second guard on top of git: these never go up


def files_to_send() -> list[Path]:
    tracked = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    out = [Path(p) for p in tracked.decode().split("\0") if p]
    out += sorted(p.relative_to(ROOT) for p in (ROOT / "demo_cache").glob("*.npz"))
    return [p for p in out if not p.name.endswith(NEVER) and (ROOT / p).is_file()]


def stage(files: list[Path], into: Path):
    for rel in files:
        dst = into / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, dst)
    shutil.copy2(ROOT / "docs" / "SPACE_CARD.md", into / "README.md")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--space", help=f"owner/name; default: your Hugging Face user/{SPACE_NAME}")
    ap.add_argument("--upload", action="store_true", help="really upload (without it, only list the files)")
    args = ap.parse_args()

    files = files_to_send()
    size = sum((ROOT / p).stat().st_size for p in files)
    demos = sum(1 for p in files if p.suffix == ".npz")
    print(f"{len(files)} files, {size / 1e6:.1f} MB, {demos} demo image files")
    if not args.upload:
        for p in files:
            print("  ", p.as_posix())
        print("\nDry run. Add --upload to send them.")
        return

    from huggingface_hub import HfApi
    api = HfApi()
    space = args.space or f"{api.whoami()['name']}/{SPACE_NAME}"
    api.create_repo(space, repo_type="space", space_sdk="docker", exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        stage(files, Path(tmp))
        api.upload_folder(folder_path=tmp, repo_id=space, repo_type="space",
                          commit_message="Update from github.com/kishorkishor/what-changed-here")
    print(f"Uploaded. The Space builds now: https://huggingface.co/spaces/{space}")
    print("Then add MODEL_API_KEY (and FIRMS_MAP_KEY) under Settings, Variables and secrets, as secrets.")


if __name__ == "__main__":
    sys.exit(main())
