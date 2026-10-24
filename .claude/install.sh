#!/usr/bin/env bash
set -euo pipefail

source_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
target_directory="${HOME}/.claude"
force="no"
if [ "${1:-}" = "--force" ]; then
  force="yes"
fi

mkdir -p "${target_directory}"

python3 - "${source_directory}" "${target_directory}" "${force}" <<'PYTHON'
import hashlib
import json
import shutil
import sys
from pathlib import Path

source_directory = Path(sys.argv[1])
target_directory = Path(sys.argv[2])
is_forced = sys.argv[3] == "yes"
manifest_path = target_directory / ".workflow-manifest.json"
managed_folders = ("agents", "commands", "skills", "workflow", "scripts")
skipped_parts = {"__pycache__", ".pytest_cache"}
retired_files = (
    "commands/map-library.md",
    "agents/doc-auditor.md",
    "agents/skill-mapper.md",
)


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def list_source_files():
    files = ["CLAUDE.md"]
    for folder in managed_folders:
        files += [
            path.relative_to(source_directory).as_posix()
            for path in sorted((source_directory / folder).rglob("*"))
            if path.is_file() and skipped_parts.isdisjoint(path.parts)
        ]
    return files


previous_manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
source_files = list_source_files()
changed_since_install = [
    relative_path
    for relative_path, installed_hash in previous_manifest.items()
    if (target_directory / relative_path).is_file()
    and file_hash(target_directory / relative_path) != installed_hash
]
if len(changed_since_install) > 0 and not is_forced:
    print("These files in ~/.claude changed since the last install (for example by /retro):")
    for relative_path in changed_since_install:
        print(f"  {relative_path}")
    print("Copy the changes you want to keep into the repo's .claude/ folder first, then run: bash install.sh --force")
    sys.exit(1)

stale_files = [
    *(relative_path for relative_path in previous_manifest if relative_path not in source_files),
    *retired_files,
]
for relative_path in stale_files:
    (target_directory / relative_path).unlink(missing_ok=True)

new_manifest = {}
for relative_path in source_files:
    source_path = source_directory / relative_path
    target_path = target_directory / relative_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_path, target_path)
    new_manifest[relative_path] = file_hash(target_path)
manifest_path.write_text(json.dumps(new_manifest, indent=2) + "\n", encoding="utf-8")

settings_path = target_directory / "settings.json"
source_hooks = json.loads((source_directory / "settings.json").read_text(encoding="utf-8"))["hooks"]
target_settings = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.is_file() else {}
target_hooks = target_settings.setdefault("hooks", {})


def is_workflow_entry(entry):
    return any(
        ".claude/scripts/hooks/" in hook.get("command", "")
        for hook in entry.get("hooks", [])
    )


for event, entries in source_hooks.items():
    kept_entries = [
        entry
        for entry in target_hooks.get(event, [])
        if not is_workflow_entry(entry)
    ]
    target_hooks[event] = kept_entries + entries
settings_path.write_text(json.dumps(target_settings, indent=2) + "\n", encoding="utf-8")
print(f"Copied {len(source_files)} files, removed {len(stale_files)} stale ones.")
PYTHON

echo "Installed the workflow into ${target_directory} and merged its hooks into ${target_directory}/settings.json."
