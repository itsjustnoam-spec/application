"""
Print a conventions reviewer's checklist with the checker's answers filled in, or validate a finished review.

:author: Noam
:date: 23/10/26
"""
# ----- Imports ----- #

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from check_python_conventions import check_changed_python_file
from check_vue_conventions import FRONTEND_SUFFIXES, check_changed_vue_file

# ----- Consts ----- #

SKILLS_DIRECTORY = Path(__file__).resolve().parent.parent / "skills"
CHECKLIST_ITEM_PATTERN = re.compile(r"^- \[ \] ([A-Z]+-\d+) (.*)$")
ANSWER_PATTERN = re.compile(
    r"^\s+- (?:(?:✅|❌)\s+(?:checker:|.*`[^`]*[./][^`]*`)|N/A\S*\s+\S.{9,})",
)
DESCRIPTION = "Print the checklist skeleton for a conventions reviewer, or validate a finished review file."
SKILLS_HELP = "Comma-separated convention skills, e.g. python-conventions,sql-conventions."
FILES_HELP = "The changed files the reviewer checks."
SINCE_HELP = "The git ref the branch is compared to ('auto': the feature's base or the merge base)."
VALIDATE_HELP = "A finished review file: report every checklist item that has no answer."
CLEAN_AUTO_ANSWER = "  - ✅ checker: no violations on the lines this branch wrote"
TODO_ANSWER ="  - TODO: ✅ `file:line` + what you saw, ❌ `file:line` (F-C<k>-<n>), or N/A + reason"

# ----- Classes ----- #


@dataclass(frozen=True)
class ChecklistItem:
    """
    One item of a skill's checklist.
    """
    rule_id: str
    text: str

    def is_automatic(self) -> bool:
        """
        Check whether the convention checker answers this item.

        :return: Whether the item is marked (auto) in the checklist.
        """
        return "(auto)" in self.text

# ----- Functions ----- #


def read_checklist(skill: str) -> list[ChecklistItem]:
    """
    Read the items of one skill's checklist, in order.

    :param skill: The skill's folder name, e.g. `python-conventions`.
    :return: Every `- [ ] ID text` item of the skill's references/checklist.md.
    """
    checklist_path = SKILLS_DIRECTORY / skill / "references" / "checklist.md"
    if not checklist_path.is_file():
        return []

    items: list[ChecklistItem] = []
    checklist_text = checklist_path.read_text(encoding="utf-8")
    for line in checklist_text.splitlines():
        item_match = CHECKLIST_ITEM_PATTERN.match(line)
        if item_match is None:
            continue

        item = ChecklistItem(
            item_match.group(1),
            item_match.group(2),
        )
        items.append(item)
    return items


def collect_violations(files: list[Path], since: str) -> dict[str, list[str]]:
    """
    Run the convention checkers on the changed files.

    :param files: The changed files.
    :param since: The git ref the branch is compared to, or `auto`.
    :return: The `path:line` of every violation, grouped by rule ID.
    """
    locations_by_rule: dict[str, list[str]] = {}
    for path in files:
        if path.suffix == ".py":
            violations = check_changed_python_file(path, since)
        elif path.suffix in FRONTEND_SUFFIXES:
            violations = check_changed_vue_file(path, since)
        else:
            continue

        for violation in violations:
            location = f"`{violation.path}:{violation.line}`"
            rule_locations = locations_by_rule.setdefault(
                violation.rule_id,
                [],
            )
            rule_locations.append(location)
    return locations_by_rule


def build_answer(item: ChecklistItem, locations_by_rule: dict[str, list[str]]) -> str:
    """
    Write the pre-filled answer line of one checklist item.

    :param item: The checklist item.
    :param locations_by_rule: The checker's violations by rule ID.
    :return: The checker's ❌ when it found violations, its ✅ for a clean automatic item, or a TODO line.
    """
    locations = locations_by_rule.get(item.rule_id, [])
    if len(locations) > 0:
        return f"  - ❌ checker: {', '.join(locations)} (add one finding per location)"

    if item.is_automatic():
        return CLEAN_AUTO_ANSWER

    return TODO_ANSWER


def print_skeleton(
    skills: list[str],
    files: list[Path],
    since: str,
) -> int:
    """
    Print the checklist section of a conventions review, with the checker's answers filled in.

    :param skills: The reviewer's skills.
    :param files: The changed files.
    :param since: The git ref the branch is compared to, or `auto`.
    :return: The exit code (always 0).
    """
    locations_by_rule = collect_violations(files, since)
    lines = ["## Checklist"]
    for skill in skills:
        lines.append(f"### {skill}")
        for item in read_checklist(skill):
            lines.append(f"- {item.rule_id} {item.text}")
            lines.append(build_answer(item, locations_by_rule))
    output = "\n".join(lines) + "\n"
    sys.stdout.buffer.write(output.encode("utf-8"))
    return 0


def find_unanswered_items(skills: list[str], review_text: str) -> list[str]:
    """
    Find the checklist items a review file leaves out or leaves unanswered.

    :param skills: The reviewer's skills.
    :param review_text: The text of the review file.
    :return: The IDs of items with no line, or whose line isn't followed by a ✅, ❌, or N/A answer.
    """
    review_lines = review_text.splitlines()
    unanswered_ids: list[str] = []
    for skill in skills:
        for item in read_checklist(skill):
            item_prefix = f"- {item.rule_id} "
            item_indexes = [
                index
                for index, line in enumerate(review_lines)
                if line.startswith(item_prefix)
            ]
            next_lines = [
                review_lines[index + 1]
                for index in item_indexes
                if index + 1 < len(review_lines)
            ]
            is_answered = any(
                ANSWER_PATTERN.match(next_line) is not None
                for next_line in next_lines
            )
            if not is_answered:
                unanswered_ids.append(item.rule_id)
    return unanswered_ids


def validate_review(skills: list[str], review_path: Path) -> int:
    """
    Check that a finished review answers every item of its skills' checklists.

    :param skills: The reviewer's skills.
    :param review_path: The review file.
    :return: 0 when every item is answered, 1 otherwise.
    """
    review_text = review_path.read_text(encoding="utf-8")
    unanswered_ids = find_unanswered_items(skills, review_text)
    if len(unanswered_ids) == 0:
        print(f"{review_path}: every checklist item is answered.")
        return 0

    missing_ids = ", ".join(unanswered_ids)
    message = f"{review_path}: these items are missing or unanswered: {missing_ids}"
    print(message)
    return 1


def main() -> int:
    """
    Print the skeleton, or validate a review file.
    """
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument(
        "--skills",
        required=True,
        help=SKILLS_HELP,
    )
    parser.add_argument(
        "--files",
        nargs="*",
        default=[],
        help=FILES_HELP,
    )
    parser.add_argument(
        "--since",
        default="auto",
        help=SINCE_HELP,
    )
    parser.add_argument(
        "--validate",
        default=None,
        help=VALIDATE_HELP,
    )
    parsed_arguments = parser.parse_args()
    skills = [
        skill.strip()
        for skill in parsed_arguments.skills.split(",")
        if skill.strip() != ""
    ]
    if parsed_arguments.validate is not None:
        review_path = Path(parsed_arguments.validate)
        return validate_review(skills, review_path)

    files = [
        Path(raw_path)
        for raw_path in parsed_arguments.files
        if Path(raw_path).is_file()
    ]
    return print_skeleton(
        skills,
        files,
        parsed_arguments.since,
    )


if __name__ == "__main__":
    sys.exit(main())
