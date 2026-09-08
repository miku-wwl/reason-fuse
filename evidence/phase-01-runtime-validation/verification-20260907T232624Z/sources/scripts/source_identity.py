"""Create a nonsecret build identity, or audit an actual native azd upload ZIP."""
import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.support.validation import Evidence

IDENTITY = ROOT / "src/reasonfuse/validation/build_identity.json"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main(evidence):
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path)
    args = parser.parse_args()
    files = sorted([p for p in (ROOT / "src").rglob("*") if p.is_file() and "__pycache__" not in p.parts and p != IDENTITY]
                   + [ROOT / p for p in [".agentignore", ".gitattributes", ".gitignore", "azure.yaml", "pyproject.toml", "requirements.txt", "uv.lock"]])
    manifest = {p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in files}
    build = {"git_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
             "source_manifest_sha256": digest(json.dumps(manifest, sort_keys=True).encode()), "files": manifest}
    if args.package:
        with zipfile.ZipFile(args.package) as archive:
            members = {i.filename: digest(archive.read(i)) for i in archive.infolist() if not i.is_dir()}
            expected = {**manifest, IDENTITY.relative_to(ROOT).as_posix(): digest(IDENTITY.read_bytes())}
            assert members == expected, f"Package mismatch: extra={members.keys()-expected.keys()}, missing={expected.keys()-members.keys()}"
            identity = json.loads(archive.read(IDENTITY.relative_to(ROOT).as_posix()))
            assert identity == build, "Stale embedded build identity"
        evidence.write("PACKAGE_MANIFEST", package=str(args.package), sha256=digest(args.package.read_bytes()), files=members, build=build)
    else:
        IDENTITY.write_text(json.dumps(build, indent=2) + "\n", encoding="utf-8")
        evidence.write("BUILD_IDENTITY", **build)
        evidence.write("WORKTREE", status=subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True),
                       diff=subprocess.check_output(["git", "diff", "--", "src", "scripts", "tests", ".agentignore"], cwd=ROOT, text=True))
    evidence.write("RESULT", status="PASS", exit_code=0)
    print(f"SOURCE_IDENTITY {build['source_manifest_sha256']} {evidence.path}")


if __name__ == "__main__":
    evidence = Evidence("source-identity")
    try:
        main(evidence)
    except Exception as error:
        evidence.write("RESULT", status="FAIL", error_type=type(error).__name__, error=str(error), exit_code=1)
        raise
