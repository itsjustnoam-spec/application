import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

from check_python_conventions import check_changed_python_file, check_python_file

HEADER = '"""\nService manager for entities.\n\n:author: Noam\n:date: 16/10/26\n"""\n'

COMPLIANT_SOURCE = HEADER + '''# ----- Imports ----- #

from app.models import Entity

# ----- Consts ----- #

PAGE_SIZE = 50

# ----- Classes ----- #


class EntityNotFoundError(Exception):
    """
    Raised when the entity does not exist.
    """
    pass


class AssetType(SQLModel, table=True):
    """
    A kind of asset.
    """
    __tablename__ = "asset_types"

    id: int | None = Field(default=None, primary_key=True)
    name: str

    __table_args__ = (UniqueConstraint("name"),)

# ----- Functions ----- #


def read_entity_by_id(session: Session, entity_id: int) -> Entity:
    """
    Read one entity by its id.
    """
    entity = session.get(Entity, entity_id)
    if entity is None:
        raise EntityNotFoundError(f"Entity {entity_id} not found.")

    return entity


def find_entity_name(entity_id: int) -> str | None:
    """
    Find the name of an entity.
    """
    if entity_id < 0:
        return None

    return "name"


def archive_entity(entity: Entity):
    """
    Archive an entity.
    """
    if entity.is_archived:
        return

    entity.is_archived = True


def list_entity_names(entities: list[Entity]) -> list[str]:
    """
    List the names of the active entities.
    """
    return [
        entity.name
        for entity in entities
        if not entity.is_archived
    ]


@router.get("/entities")
def list_entities(
    session: Annotated[Session, Depends(get_session)],
    query: Annotated[str | None, Query(alias="q")] = None,
) -> list[Entity]:
    """
    List entities matching the search text.
    """
    transaction = session.begin()
    entities = search_entities(session, query)
    transaction.rollback()
    return entities


def build_entity_query(
    session: Session,
    entity_type: str,
    page_size: int,
) -> Query:
    """
    Build the query that lists entities.
    """
    return session.query(
        entity_type,
        page_size,
        Entity,
    )
'''


def rule_ids(path: Path) -> list[str]:
    return [
        violation.rule_id
        for violation in check_python_file(path)
    ]


def test_check_python_file_compliant_source_returns_no_violations(write_python_file: Callable[..., Path]):
    path = write_python_file(COMPLIANT_SOURCE)

    violations = check_python_file(path)

    assert violations == []


def test_check_python_file_empty_file_returns_no_violations(write_python_file: Callable[..., Path]):
    path = write_python_file("", "__init__.py")

    violations = check_python_file(path)

    assert violations == []


@pytest.mark.parametrize("snippet,expected_rule_id", [
    ("def save_entity(entity):\n    print(entity)\n", "PY-01"),
    ("def save_entity(entity: int) -> None:\n    print(entity)\n", "PY-02"),
    ("def save_entity(entity: int):\n    if entity > 0:\n        return None\n    print(entity)\n", "PY-03"),
    ("def save_entity(entity: int):\n    print(entity)\n    return\n", "PY-04"),
    ("__all__ = ['save_entity']\n", "PY-13"),
    ("def save_entity(entity: int):\n    '''Saves.'''\n", "PY-14"),
    ("raise ValueError('bad')\n", "PY-25"),
    ("class EntityMissing(Exception):\n    pass\n", "PY-26"),
    ("save_entity(first, second, third)\n", "PY-24"),
    ("save_entity(entity_identifier_value, replacement_value_for_the_entity_name)\n", "PY-24"),
    ("def save_entity(entity: int):\n    if entity > 0:\n        print(entity)\n    print(entity)\n", "PY-32"),
    ('class Store:\n    """\n    Store.\n    """\n\n    items = 1\n', "PY-29"),
    ("class Asset(SQLModel, table=True):\n    name: str\n    __tablename__ = 'assets'\n", "PY-30"),
    ("class Asset(SQLModel, table=True):\n    __table_args__ = ()\n    name: str\n", "PY-31"),
    ("def save_entity(entity: int):\n    print(entity)\n", "PY-35"),
    ("class Store:\n    def count_items(self) -> int:\n        return 1\n", "PY-35"),
    ('def run_jobs():\n    """\n    Runs jobs.\n    """\n\n    def run_one():\n        print(1)\n\n    run_one()\n', "PY-35"),
    ("def save_entity(q: str):\n    print(q)\n", "PY-36"),
    ("try:\n    save()\nexcept OSError as e:\n    print(e)\n", "PY-36"),
    ("db = connect()\n", "PY-36"),
    ("SessionDep = Annotated[Session, Depends(get_session)]\n", "PY-37"),
    ("session_dependency = Depends(get_session)\n", "PY-37"),
    ("names = [site.name for site in sites]\n", "PY-38"),
    ("names = [\n    site.name for site in sites\n]\n", "PY-38"),
    ("found = any(line == '' for line in lines)\n", "PY-38"),
    ('class SiteError(Exception):\n    """\n    Site failure.\n    """\n', "PY-39"),
    ("session.rollback()\n", "PY-40"),
    ("self.session.rollback()\n", "PY-40"),
    ('def lock_resource(resource: int):\n    """\n    Locks the resource.\n    """\n    print(resource)\n', "PY-41"),
    ('def is_overdue(day: int) -> bool:\n    """\n    Check whether the day passed.\n\n    :param day: Day.\n    :return: True when the day passed, False otherwise.\n    """\n    return day > 0\n', "PY-42"),
    ("class AssetStatus(str, Enum):\n    pass\n", "PY-43"),
    ("STATUSES = [AssetStatus.OUT_OF_SERVICE, AssetStatus.RETIRED]\n", "PY-44"),
    ("STATUSES = frozenset(\n    {AssetStatus.OUT_OF_SERVICE, AssetStatus.RETIRED},\n)\n", "PY-44"),
    ("STATUSES = [\n    AssetStatus.OUT_OF_SERVICE, AssetStatus.RETIRED,\n]\n", "PY-44"),
    ("value = 1  # explain the value\n", "PY-52"),
    ("# explain the next line\nvalue = 1\n", "PY-52"),
    ("value = compute()  # noqa: E501\n", "PY-53"),
    ("value = compute()  # type: ignore[arg-type]\n", "PY-53"),
    ("value = manager._build_query()\n", "PY-54"),
    ("from app.entities import _build_query\n", "PY-54"),
    ("STATUS_KEY = 'status'\n", "PY-55"),
    ("DIALOG_WIDTH = '40rem'\n", "PY-55"),
    ("print('the entity could not be saved')\n", "PY-34"),
    ("API_URL = 'https://api.example.com/v1'\n", "PY-33"),
    ("connect('localhost')\n", "PY-33"),
    ("class Site(SQLModel):\n    @field_validator('name')\n    def strip_name(cls, name: str) -> str:\n        return name\n", "PY-46"),
    ("if kind == 'a':\n    run_a()\nelif kind == 'b':\n    run_b()\nelif kind == 'c':\n    run_c()\n", "PY-47"),
    ("class Asset(SQLModel, table=True):\n    __tablename__ = 'assets'\n\n    name: str = Field(index=True)\n", "SQL-04"),
    ("value = Wrapper(max(first, second, third))\n", "PY-24"),
])
def test_check_python_file_violating_snippet_reports_rule(
    write_python_file: Callable[..., Path],
    snippet: str,
    expected_rule_id: str,
):
    path = write_python_file(HEADER + "# ----- Imports ----- #\n\nimport os\n\n# ----- Functions ----- #\n\n\n" + snippet)

    reported_rule_ids = rule_ids(path)

    assert expected_rule_id in reported_rule_ids


@pytest.mark.parametrize("source,expected_rule_id", [
    ("import os\n", "PY-07"),
    ('"""\nNo author or date.\n"""\nimport os\n', "PY-07"),
    (HEADER + "\n# ----- Imports ----- #\n\nimport os\n", "PY-09"),
    (HEADER + "# ----- Imports ----- #\nimport os\n", "PY-09"),
    (HEADER + "# ----- Imports ----- #\n\nimport os\n# ----- Consts ----- #\n\nSIZE = 1\n", "PY-10"),
    (HEADER + "# ----- Imports ----- #\n\nimport os\n\n# ----- Functions ----- #\n\ndef run():\n    print(1)\n", "PY-11"),
    (HEADER + "# ----- imports ----- #\n\nimport os\n", "PY-08"),
    (HEADER + "# ---- Imports ---- #\n\nimport os\n", "PY-08"),
])
def test_check_python_file_bad_layout_reports_rule(
    write_python_file: Callable[..., Path],
    source: str,
    expected_rule_id: str,
):
    path = write_python_file(source)

    reported_rule_ids = rule_ids(path)

    assert expected_rule_id in reported_rule_ids


def test_check_python_file_blank_line_between_docstring_fields_reports_py15(write_python_file: Callable[..., Path]):
    snippet = 'def save_entity(entity: int) -> int:\n    """\n    Saves.\n\n    :param entity: Id.\n\n    :return: Id.\n    """\n    return entity\n'
    path = write_python_file(HEADER + "# ----- Imports ----- #\n\nimport os\n\n# ----- Functions ----- #\n\n\n" + snippet)

    reported_rule_ids = rule_ids(path)

    assert "PY-15" in reported_rule_ids


def test_check_python_file_init_docstring_reports_py16(write_python_file: Callable[..., Path]):
    snippet = 'class Store:\n    """\n    Store.\n    """\n\n    def __init__(self):\n        """\n        Builds.\n        """\n        self.items = 1\n'
    path = write_python_file(HEADER + "# ----- Imports ----- #\n\nimport os\n\n# ----- Classes ----- #\n\n\n" + snippet)

    reported_rule_ids = rule_ids(path)

    assert "PY-16" in reported_rule_ids


def test_check_python_file_utf8_bom_reports_py00(tmp_path: Path):
    path = tmp_path / "module.py"
    path.write_bytes(b"\xef\xbb\xbf" + COMPLIANT_SOURCE.encode("utf-8"))

    reported_rule_ids = rule_ids(path)

    assert reported_rule_ids == ["PY-00"]


def test_check_python_file_test_module_skips_layout_rules(write_python_file: Callable[..., Path]):
    path = write_python_file(
        "import pytest\n\n@pytest.mark.parametrize('value,expected', [\n    (1, 2),\n    (2, 3),\n])\ndef test_increment(value, expected):\n    assert value + 1 == expected\n",
        "test_increment.py",
    )

    violations = check_python_file(path)

    assert violations == []


def test_check_python_file_syntax_error_reports_syntax_rule(write_python_file: Callable[..., Path]):
    path = write_python_file("def broken(:\n")

    reported_rule_ids = rule_ids(path)

    assert reported_rule_ids == ["PY-SYNTAX"]


@pytest.mark.parametrize("snippet", [
    "save_entity(entity_identifier, replacement_value)\n",
    "if is_ready:\n    publish()\n",
    "if is_ready:\n    publish()\n\nnotify()\n",
    "if is_ready:\n    publish()\nelse:\n    wait()\n\nnotify()\n",
    "STATUSES = frozenset(\n    {\n        AssetStatus.OUT_OF_SERVICE,\n        AssetStatus.RETIRED,\n    },\n)\n",
    "handlers: dict[str, Callable[[int, str], bool]] = {}\n",
    "NAMES = ['single']\n",
    "NAMES = ['North', 'South']\n",
    "assert names == ['Compressor', 'Pump ABC']\n",
])
def test_check_python_file_compliant_snippet_reports_nothing(
    write_python_file: Callable[..., Path],
    snippet: str,
):
    path = write_python_file(HEADER + "# ----- Imports ----- #\n\nimport os\n\n# ----- Functions ----- #\n\n\n" + snippet)

    violations = check_python_file(path)

    assert violations == []


def test_check_python_file_long_line_with_several_calls_reports_it_once(
    write_python_file: Callable[..., Path],
):
    snippet = "location = (line_match.group('path_value'), line_match.group('line_value'))\n"
    path = write_python_file(HEADER + "# ----- Imports ----- #\n\nimport os\n\n# ----- Functions ----- #\n\n\n" + snippet)

    reported_rule_ids = rule_ids(path)

    assert reported_rule_ids == ["PY-24"]


@pytest.mark.parametrize("directory", [
    "migrations",
    "versions",
])
def test_check_python_file_migration_file_is_exempt(tmp_path: Path, directory: str):
    path = tmp_path / "alembic" / directory / "0001_create_assets.py"
    path.parent.mkdir(parents=True)
    path.write_text("def upgrade() -> None:\n    op.create_table('assets')\n", encoding="utf-8")

    violations = check_python_file(path)

    assert violations == []



@pytest.mark.parametrize("source,expected_rule_id", [
    ('"""\nTests for sites.\n"""\nimport pytest\n', "TS-27"),
    ("import pytest\n\n# ----- Tests ----- #\n", "TS-27"),
    ("def test_archive_site(session):\n    session.add(Site(name='a'))\n", "TS-28"),
    ("def test_archive_site(db_session):\n    db_session.commit()\n", "TS-28"),
    ("def test_archive_site(db_session):\n    assert db_session.get(Site, 1) is None\n", "TS-28"),
])
def test_check_python_file_test_module_violation_reports_rule(
    write_python_file: Callable[..., Path],
    source: str,
    expected_rule_id: str,
):
    path = write_python_file(source, "test_sites.py")

    reported_rule_ids = rule_ids(path)

    assert expected_rule_id in reported_rule_ids


def test_check_python_file_conftest_env_fixture_may_write_through_session(
    write_python_file: Callable[..., Path],
):
    source = "def env(db_session):\n    db_session.add(Site(name='a'))\n    db_session.flush()\n"
    path = write_python_file(source, "conftest.py")

    violations = check_python_file(path)

    assert violations == []


def test_check_python_file_conftest_factory_outside_env_reports_ts30(
    write_python_file: Callable[..., Path],
):
    source = "def make_site(db_session):\n    db_session.add(Site(name='a'))\n"
    path = write_python_file(source, "conftest.py")

    reported_rule_ids = rule_ids(path)

    assert reported_rule_ids == ["TS-30"]


def test_check_python_file_banner_text_inside_string_is_ignored(
    write_python_file: Callable[..., Path],
):
    source = 'SOURCE = """\n# ----- Imports ----- #\n"""\n'
    path = write_python_file(source, "test_banners.py")

    violations = check_python_file(path)

    assert violations == []


def test_check_python_file_raise_in_models_library_reports_py48(tmp_path: Path):
    path = tmp_path / "midnight_models" / "site.py"
    path.parent.mkdir(parents=True)
    path.write_text(HEADER + "# ----- Imports ----- #\n\nimport os\n\n# ----- Functions ----- #\n\n\nraise SiteError('bad')\n", encoding="utf-8")

    reported_rule_ids = rule_ids(path)

    assert "PY-48" in reported_rule_ids


def test_check_python_file_raise_in_application_is_allowed(write_python_file: Callable[..., Path]):
    path = write_python_file(HEADER + "# ----- Imports ----- #\n\nimport os\n\n# ----- Functions ----- #\n\n\nraise SiteError('bad')\n")

    reported_rule_ids = rule_ids(path)

    assert "PY-48" not in reported_rule_ids


@pytest.mark.parametrize("snippet,unexpected_rule_id", [
    ("value = self._build_query()\n", "PY-54"),
    ("value = super()._build_query()\n", "PY-54"),
    ("value = point._replace(x=1)\n", "PY-54"),
    ("value = entity.__class__\n", "PY-54"),
    ("MESSAGE = 'the entity could not be saved'\n", "PY-34"),
    ("print('Site not found')\n", "PY-34"),
    ("PAGE_SIZE = 50\n", "PY-55"),
    ("if kind == 'a':\n    run_a()\nelif kind == 'b':\n    run_b()\n", "PY-47"),
    ('def make_alias(name: str) -> str:\n    """\n    Alias the name.\n    """\n    return name\n', "PY-41"),
])
def test_check_python_file_allowed_snippet_does_not_report_rule(
    write_python_file: Callable[..., Path],
    snippet: str,
    unexpected_rule_id: str,
):
    path = write_python_file(HEADER + "# ----- Imports ----- #\n\nimport os\n\n# ----- Functions ----- #\n\n\n" + snippet)

    reported_rule_ids = rule_ids(path)

    assert unexpected_rule_id not in reported_rule_ids


def test_check_python_file_session_suffix_in_test_reports_ts28(write_python_file: Callable[..., Path]):
    path = write_python_file("def test_save(db_session):\n    db_session.add(1)\n", "test_save.py")

    reported_rule_ids = rule_ids(path)

    assert "TS-28" in reported_rule_ids


def test_check_python_file_http_session_in_test_is_allowed(write_python_file: Callable[..., Path]):
    path = write_python_file("def test_save(http_session):\n    http_session.get(1)\n", "test_save.py")

    reported_rule_ids = rule_ids(path)

    assert "TS-28" not in reported_rule_ids


def run_git(repository: Path, *arguments: str):
    subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        stdin=subprocess.DEVNULL,
        capture_output=True,
    )


def create_repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repo"
    repository.mkdir()
    run_git(repository, "init", "-q")
    run_git(repository, "config", "user.email", "test@example.com")
    run_git(repository, "config", "user.name", "Test")
    (repository / "README.md").write_text("readme\n", encoding="utf-8")
    run_git(repository, "add", ".")
    run_git(repository, "commit", "-q", "-m", "base")
    return repository


def test_check_changed_python_file_reports_only_changed_lines(tmp_path: Path):
    repository = create_repository(tmp_path)
    path = repository / "module.py"
    path.write_text("import os\nold = 1  # old comment\n", encoding="utf-8")
    run_git(repository, "add", ".")
    run_git(repository, "commit", "-q", "-m", "module")
    path.write_text("import os\nold = 1  # old comment\nnew = 2  # new comment\n", encoding="utf-8")

    violations = check_changed_python_file(path, "HEAD")

    assert [
        (violation.line, violation.rule_id)
        for violation in violations
    ] == [(3, "PY-52")]


def test_check_changed_python_file_new_file_reports_whole_file(tmp_path: Path):
    repository = create_repository(tmp_path)
    path = repository / "module.py"
    path.write_text("import os\n", encoding="utf-8")

    violations = check_changed_python_file(path, "HEAD")

    assert "PY-07" in [
        violation.rule_id
        for violation in violations
    ]
