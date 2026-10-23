import subprocess
from pathlib import Path

import pytest

from check_vue_conventions import check_changed_vue_file, check_vue_file

COMPLIANT_COMPONENT = '''<template>
  <v-card
    color="primary"
    :style="{ width: '20rem' }"
  >
    <v-btn
      :disabled="selectedSiteId === null"
      @click="selectSite"
    >
      Save site
    </v-btn>
  </v-card>
</template>

<script lang="ts">
interface Props {
  siteName: string
}

interface Emits {
  'select': [number]
}

const EMPTY_MESSAGE = 'There are no sites yet.'
</script>

<script setup lang="ts">
const emit = defineEmits<Emits>()

const props = defineProps<Props>()

const selectedSiteId = ref<number | null>(null)

const selectSite = (): void => {
  if (selectedSiteId.value === null) {
    return
  }

  emit('select', selectedSiteId.value)
}
</script>

<style scoped>
.site-card {
  color: rgb(var(--v-theme-primary));
}
</style>
'''


def write_file(tmp_path: Path, name: str, source: str) -> Path:
    path = tmp_path / name
    path.write_text(source, encoding="utf-8")
    return path


def rule_ids(path: Path) -> list[str]:
    return [
        violation.rule_id
        for violation in check_vue_file(path)
    ]


def test_check_vue_file_compliant_component_returns_no_violations(tmp_path: Path):
    path = write_file(tmp_path, "SiteCard.vue", COMPLIANT_COMPONENT)

    violations = check_vue_file(path)

    assert violations == []


@pytest.mark.parametrize("snippet,expected_rule_id", [
    ("const siteName = site.name ?? 'Unknown'\n", "VU-33"),
    ("const siteName = site?.name\n", "VU-33"),
    ("const hasSites = !!sites.length\n", "VU-33"),
    ("const siteName = site.name || 'Unknown'\n", "VU-33"),
    ("const sites = response.items || []\n", "VU-33"),
    ("void loadSites()\n", "VU-35"),
    ("const total = 1 // the total\n", "VU-40"),
    ("/* the total */\nconst total = 1\n", "VU-40"),
    ("const ERROR_COLOR = '#ff0000'\n", "VU-16"),
    ("const rowClass = 'text-red-500'\n", "VU-16"),
    ("const SAVE_LABEL = 'Save site'\n", "VU-22"),
    ("const DIALOG_WIDTH = '40rem'\n", "VU-22"),
    ("showError('The site could not be saved')\n", "VU-22"),
])
def test_check_vue_file_violating_script_reports_rule(
    tmp_path: Path,
    snippet: str,
    expected_rule_id: str,
):
    path = write_file(tmp_path, "sites.ts", snippet)

    reported_rule_ids = rule_ids(path)

    assert expected_rule_id in reported_rule_ids


@pytest.mark.parametrize("snippet,unexpected_rule_id", [
    ("const isReady = (): void => {}\n", "VU-35"),
    ("const loadSites = async (): Promise<void> => {}\n", "VU-35"),
    ("interface Site {\n  name?: string\n}\n", "VU-33"),
    ("if (isOpen && isReady) {\n  open()\n}\n", "VU-33"),
    ("const url = 'https://example.com//path'\n", "VU-40"),
    ("const MESSAGES = {\n  empty: 'There are no sites yet.',\n}\n", "VU-22"),
    ("const color = 'rgb(var(--v-theme-primary))'\n", "VU-16"),
])
def test_check_vue_file_allowed_script_does_not_report_rule(
    tmp_path: Path,
    snippet: str,
    unexpected_rule_id: str,
):
    path = write_file(tmp_path, "sites.ts", snippet)

    reported_rule_ids = rule_ids(path)

    assert unexpected_rule_id not in reported_rule_ids


@pytest.mark.parametrize("old,new,expected_rule_id", [
    ("const emit = defineEmits<Emits>()", "const emit = defineEmits<{ select: [number] }>()", "VU-27"),
    ("const emit = defineEmits<Emits>()", "const emit = defineEmits<SiteCardEmits>()", "VU-27"),
    ("const props = defineProps<Props>()", "const props = defineProps({ siteName: String })", "VU-27"),
    ("interface Props {\n  siteName: string\n}\n", "", "VU-27"),
    ("const selectedSiteId = ref<number | null>(null)", "const MAX_SITES = 5\n\nconst selectedSiteId = ref<number | null>(null)", "VU-05"),
    ("const selectedSiteId = ref<number | null>(null)", "interface Emits {\n  'select': [number]\n}\n\nconst selectedSiteId = ref<number | null>(null)", "VU-05"),
    ("const EMPTY_MESSAGE", "export const EMPTY_MESSAGE", "VU-32"),
    ("  <v-card\n", "  <!-- the card -->\n  <v-card\n", "VU-40"),
    ('      :disabled="selectedSiteId === null"', '      :disabled="selectedSiteId ?? true"', "VU-33"),
    ('    color="primary"', '    color="red"', "VU-16"),
    ('    color="primary"', '    class="bg-blue-500"', "VU-16"),
    ("    :style=\"{ width: '20rem' }\"", '    style="color: #fff"', "VU-16"),
    ("  color: rgb(var(--v-theme-primary));", "  color: #333333;", "VU-16"),
    (".site-card {", "/* card */\n.site-card {", "VU-40"),
])
def test_check_vue_file_violating_component_reports_rule(
    tmp_path: Path,
    old: str,
    new: str,
    expected_rule_id: str,
):
    assert old in COMPLIANT_COMPONENT
    path = write_file(tmp_path, "SiteCard.vue", COMPLIANT_COMPONENT.replace(old, new, 1))

    reported_rule_ids = rule_ids(path)

    assert expected_rule_id in reported_rule_ids


def test_check_vue_file_theme_file_may_hold_colors(tmp_path: Path):
    path = write_file(tmp_path, "vuetify.ts", "const PRIMARY = '#1867c0'\n")

    reported_rule_ids = rule_ids(path)

    assert "VU-16" not in reported_rule_ids


def test_check_vue_file_test_file_may_use_long_strings(tmp_path: Path):
    path = write_file(tmp_path, "SiteCard.spec.ts", "it('shows the empty message when there are no sites', () => {})\n")

    reported_rule_ids = rule_ids(path)

    assert "VU-22" not in reported_rule_ids


def run_git(repository: Path, *arguments: str):
    subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        stdin=subprocess.DEVNULL,
        capture_output=True,
    )


def create_repository_with(tmp_path: Path, name: str, source: str) -> Path:
    repository = tmp_path / "repo"
    repository.mkdir()
    run_git(repository, "init", "-q")
    run_git(repository, "config", "user.email", "test@example.com")
    run_git(repository, "config", "user.name", "Test")
    path = repository / name
    path.write_text(source, encoding="utf-8")
    run_git(repository, "add", ".")
    run_git(repository, "commit", "-q", "-m", "base")
    return path


def test_check_changed_vue_file_reports_structure_rules_on_the_whole_touched_file(tmp_path: Path):
    old_source = COMPLIANT_COMPONENT.replace("defineEmits<Emits>()", "defineEmits<{ select: [number] }>()")
    old_source = old_source.replace("selectedSiteId === null\"", "selectedSiteId ?? true\"")
    path = create_repository_with(tmp_path, "SiteCard.vue", old_source)
    path.write_text(old_source.replace("Save site", "Save the site"), encoding="utf-8")

    reported_rule_ids = [
        violation.rule_id
        for violation in check_changed_vue_file(path, "HEAD")
    ]

    assert "VU-27" in reported_rule_ids
    assert "VU-33" not in reported_rule_ids


def test_check_changed_vue_file_untouched_file_reports_nothing(tmp_path: Path):
    old_source = COMPLIANT_COMPONENT.replace("defineEmits<Emits>()", "defineEmits<{ select: [number] }>()")
    path = create_repository_with(tmp_path, "SiteCard.vue", old_source)

    violations = check_changed_vue_file(path, "HEAD")

    assert violations == []


def test_check_changed_vue_file_reports_line_rules_on_changed_lines(tmp_path: Path):
    path = create_repository_with(tmp_path, "sites.ts", "const first = 1\n")
    path.write_text("const first = 1\nconst second = site?.name\n", encoding="utf-8")

    violations = check_changed_vue_file(path, "HEAD")

    assert [
        (violation.line, violation.rule_id)
        for violation in violations
    ] == [(2, "VU-33")]
