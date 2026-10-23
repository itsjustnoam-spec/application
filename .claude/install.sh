#!/usr/bin/env bash
set -euo pipefail

source_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
target_directory="${HOME}/.claude"
retired_files=(
  "commands/map-library.md"
  "agents/doc-auditor.md"
  "agents/skill-mapper.md"
)

mkdir -p "${target_directory}"
cp "${source_directory}/CLAUDE.md" "${target_directory}/CLAUDE.md"
for folder in agents commands skills workflow scripts; do
  mkdir -p "${target_directory}/${folder}"
  cp -R "${source_directory}/${folder}/." "${target_directory}/${folder}/"
done
find "${target_directory}/scripts" -type d \( -name "__pycache__" -o -name ".pytest_cache" \) -prune -exec rm -rf {} +
for retired_file in "${retired_files[@]}"; do
  rm -f "${target_directory}/${retired_file}"
done

python3 - "${source_directory}/settings.json" "${target_directory}/settings.json" <<'PYTHON'
import json
import sys
from pathlib import Path

source_path = Path(sys.argv[1])
target_path = Path(sys.argv[2])
source_hooks = json.loads(source_path.read_text(encoding="utf-8"))["hooks"]
target_settings = json.loads(target_path.read_text(encoding="utf-8")) if target_path.is_file() else {}
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

target_path.write_text(json.dumps(target_settings, indent=2) + "\n", encoding="utf-8")
PYTHON

echo "Installed the workflow into ${target_directory} and merged its hooks into ${target_directory}/settings.json."
