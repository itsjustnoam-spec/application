"""
Checks Python files against the house conventions that ruff and mypy cannot express.

:author: Noam
:date: 16/10/26
"""
# ----- Imports ----- #

import argparse
import ast
import builtins
import itertools
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TypeGuard

# ----- Consts ----- #

UTF8_BOM = b"\xef\xbb\xbf"
BANNER_LIKE_PATTERN = re.compile(r"^\s*#\s*-{3,}")
BANNER_PATTERN = re.compile(r"^# ----- ([A-Z][A-Za-z0-9 ]*) ----- #$")
AUTHOR_PATTERN = re.compile(r"^:author: \S", re.MULTILINE)
DATE_PATTERN = re.compile(
    r"^:date: \d{2}/\d{2}/\d{2}$",
    re.MULTILINE,
)
DOCSTRING_QUOTE_LINES = ('"""', 'r"""')
DOCSTRING_FIELD_PREFIXES = (":param", ":return", ":raises")
IMPORTS_BANNER_NAME = "Imports"
CONSTS_BANNER_NAME = "Consts"
BLANK_LINES_BELOW_BANNER = {"Imports": 1, "Consts": 1}
DEFAULT_BLANK_LINES_BELOW_BANNER = 2
BLANK_LINES_ABOVE_BANNER = 1
MULTILINE_CALL_MIN_ARGUMENTS = 3
MULTILINE_CALL_MIN_LINE_LENGTH = 70
MIGRATION_DIRECTORY_NAMES = ("migrations", "versions")
TABLE_NAME_ATTRIBUTE = "__tablename__"
TABLE_ARGS_ATTRIBUTE = "__table_args__"
SHORT_NAME_ALLOWLIST = {"_"}
ABBREVIATED_NAMES = {
    "arr",
    "cfg",
    "cnt",
    "conn",
    "ctx",
    "db",
    "dct",
    "err",
    "ex",
    "idx",
    "lst",
    "msg",
    "num",
    "obj",
    "qry",
    "req",
    "res",
    "resp",
    "sess",
    "tmp",
    "val",
}
SINGLE_TARGET_NODE_TYPES = (
    ast.AnnAssign,
    ast.AugAssign,
    ast.NamedExpr,
    ast.For,
    ast.AsyncFor,
    ast.comprehension,
)
ASSIGNMENT_NODE_TYPES = (ast.Assign, ast.AnnAssign)
SINGLE_ELEMENT_COMPREHENSION_TYPES = (
    ast.ListComp,
    ast.SetComp,
    ast.GeneratorExp,
)
COMPREHENSION_NODE_TYPES = (
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
)
DEPENDS_NAME = "Depends"
SESSION_NAME_PART = "session"
ROLLBACK_METHOD = "rollback"
SESSION_WRITE_METHODS = {
    "add",
    "add_all",
    "commit",
    "delete",
    "execute",
    "flush",
    "merge",
}
CONFTEST_FILE_NAME = "conftest.py"
ENVIRONMENT_FIXTURE_NAME = "env"
THIRD_PERSON_SUFFIX = "s"
NON_THIRD_PERSON_ENDINGS = ("ss", "us", "is")
ES_PLURAL_ENDINGS = ("ches", "shes", "sses", "xes", "zzes")
FIRST_WORD_PATTERN = re.compile(r"^([A-Za-z]+)\b")
RETURN_FIELD_PREFIX = ":return:"
BOOLEAN_RETURN_WORDS = ("true", "false")
ENUM_BASE_NAME = "Enum"
STR_BASE_NAME = "str"
COLLECTION_LITERAL_TYPES = (ast.List, ast.Set)
SMALL_COLLECTION_MAX_LENGTH = 30
SELF_ARGUMENT_NAMES = ("self", "cls")
EXCEPTION_NAME_SUFFIXES = ("Error", "Exception")
FUNCTION_NODE_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef)
NESTED_SCOPE_NODE_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)
DOCSTRING_OWNER_NODE_TYPES = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
BUILTIN_EXCEPTION_NAMES = frozenset(
    name
    for name, value in vars(builtins).items()
    if isinstance(value, type) and issubclass(value, BaseException)
)

# ----- Classes ----- #


@dataclass(frozen=True)
class Violation:
    """
    A single convention violation found in a file.
    """
    path: Path
    line: int
    rule_id: str
    message: str

    def format_for_output(self) -> str:
        """
        Format the violation as 'path:line: RULE message'.
        """
        return f"{self.path}:{self.line}: {self.rule_id} {self.message}"

# ----- Functions ----- #


def is_test_file(path: Path) -> bool:
    """
    Check whether a file is a test module, a conftest, or under tests/.
    """
    is_conftest = path.name == "conftest.py"
    is_test_module = path.name.startswith("test_") or is_conftest
    return is_test_module or "tests" in path.parts


def is_migration_file(path: Path) -> bool:
    """
    Check whether a file is a generated migration.
    """
    return any(
        part in MIGRATION_DIRECTORY_NAMES
        for part in path.parts[:-1]
    )


def is_call(node: ast.AST) -> TypeGuard[ast.Call]:
    """
    Check whether a node is a function call.
    """
    return isinstance(node, ast.Call)


def is_docstring_field(docstring_line: str) -> bool:
    """
    Check whether a docstring line starts a :param, :return, or :raises field.
    """
    stripped_line = docstring_line.strip()
    return stripped_line.startswith(DOCSTRING_FIELD_PREFIXES)


def is_single_generator_call(node: ast.Call) -> bool:
    """
    Check whether a call's only argument is a generator expression.
    """
    if len(node.args) != 1 or len(node.keywords) > 0:
        return False

    return isinstance(node.args[0], ast.GeneratorExp)


def is_statement_block(block: object) -> TypeGuard[list[ast.stmt]]:
    """
    Check whether a value is a non-empty list of statements.
    """
    if not isinstance(block, list) or len(block) == 0:
        return False

    return isinstance(block[0], ast.stmt)


def is_trailing_bare_return(statement: ast.stmt) -> bool:
    """
    Check whether a statement is a bare return.
    """
    if not isinstance(statement, ast.Return):
        return False

    return statement.value is None


def is_init_method(node: ast.AST) -> bool:
    """
    Check whether a node is an __init__ method.
    """
    if not isinstance(node, FUNCTION_NODE_TYPES):
        return False

    return node.name == "__init__"


def get_target_name(target: ast.expr) -> str | None:
    """
    Return the variable name of an assignment target, when it's a plain name.
    """
    if not isinstance(target, ast.Name):
        return None

    return target.id


def get_argument_owner_line(parent: ast.AST, child: ast.AST) -> int | None:
    """
    Return the line of the call that has the child as an argument.
    """
    if not isinstance(parent, ast.Call) or child is parent.func:
        return None

    return parent.lineno


def build_parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    """
    Map every node of a tree to its parent node.
    """
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


def iter_own_body_nodes(function_node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.AST]:
    """
    Collect every node inside a function body, without descending into nested scopes.

    :param function_node: The function whose own body is walked.
    :return: All nodes that belong to the function itself.
    """
    own_nodes: list[ast.AST] = []
    pending_nodes: list[ast.AST] = list(function_node.body)
    while len(pending_nodes) > 0:
        node = pending_nodes.pop()
        own_nodes.append(node)
        if isinstance(node, NESTED_SCOPE_NODE_TYPES):
            continue

        pending_nodes.extend(ast.iter_child_nodes(node))
    return own_nodes


def is_none_constant(node: ast.AST | None) -> bool:
    """
    Check whether a node is the constant None.
    """
    return isinstance(node, ast.Constant) and node.value is None


def function_returns_value(function_node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """
    Check whether a function returns a real value or is a generator.

    :param function_node: The function to inspect.
    :return: Whether any own `return` carries a non-None value or the function yields.
    """
    for node in iter_own_body_nodes(function_node):
        if isinstance(node, (ast.Yield, ast.YieldFrom)):
            return True

        if not isinstance(node, ast.Return) or node.value is None:
            continue

        if not is_none_constant(node.value):
            return True
    return False


def get_called_name(node: ast.AST) -> str | None:
    """
    Return the plain name of a called function or method.
    """
    if isinstance(node, ast.Call):
        node = node.func

    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        return node.attr

    return None


def annotation_allows_none(annotation: ast.expr | None) -> bool:
    """
    Check whether a return annotation allows None.
    """
    if annotation is None:
        return False

    for node in ast.walk(annotation):
        is_optional = get_called_name(node) == "Optional"
        if is_none_constant(node) or is_optional:
            return True
    return False


def get_docstring_node(node: ast.AST) -> ast.Constant | None:
    """
    Return the docstring constant of a module, class, or function.
    """
    body = getattr(
        node,
        "body",
        None,
    )
    if not isinstance(body, list) or len(body) == 0:
        return None

    first_statement = body[0]
    if not isinstance(first_statement, ast.Expr):
        return None

    docstring_value = first_statement.value
    if not isinstance(docstring_value, ast.Constant):
        return None

    if isinstance(docstring_value.value, str):
        return docstring_value

    return None


def count_blank_lines_above(lines: list[str], index: int) -> int:
    """
    Count the blank lines right above a line.
    """
    blank_count = 0
    cursor = index - 1
    while cursor >= 0 and lines[cursor].strip() == "":
        blank_count += 1
        cursor -= 1
    return blank_count


def count_blank_lines_below(lines: list[str], index: int) -> int:
    """
    Count the blank lines right below a line.
    """
    blank_count = 0
    cursor = index + 1
    while cursor < len(lines) and lines[cursor].strip() == "":
        blank_count += 1
        cursor += 1
    return blank_count


def read_source_segment(
    line_bytes: list[bytes],
    start: tuple[int, int],
    end: tuple[int, int],
) -> str:
    """
    Read source text between two AST positions (1-based lines, UTF-8 byte columns).

    :param line_bytes: The file's lines encoded as UTF-8.
    :param start: The (line, column) where the segment starts.
    :param end: The (line, column) where the segment ends.
    :return: The decoded text between the two positions.
    """
    start_line, start_column = start
    end_line, end_column = end
    if start_line == end_line:
        line = line_bytes[start_line - 1]
        return line[start_column:end_column].decode("utf-8")

    parts = [line_bytes[start_line - 1][start_column:]]
    parts.extend(line_bytes[start_line:end_line - 1])
    parts.append(line_bytes[end_line - 1][:end_column])
    return b"\n".join(parts).decode("utf-8")


def check_encoding(path: Path, raw_source: bytes) -> list[Violation]:
    """
    Check that the file doesn't start with a UTF-8 BOM.
    """
    if not raw_source.startswith(UTF8_BOM):
        return []

    violation = Violation(
        path,
        1,
        "PY-00",
        "File starts with a UTF-8 BOM; save it as UTF-8 without BOM.",
    )
    return [violation]


def check_parameter_annotations(
    path: Path,
    tree: ast.Module,
    parents: dict[ast.AST, ast.AST],
) -> list[Violation]:
    """
    Check that every function parameter has a type annotation.
    """
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if not isinstance(node, FUNCTION_NODE_TYPES):
            continue

        arguments = [
            *node.args.posonlyargs,
            *node.args.args,
            *node.args.kwonlyargs,
        ]
        if node.args.vararg is not None:
            arguments.append(node.args.vararg)

        if node.args.kwarg is not None:
            arguments.append(node.args.kwarg)

        is_method = isinstance(parents.get(node), ast.ClassDef)
        for position, argument in enumerate(arguments):
            if is_method and position == 0 and argument.arg in SELF_ARGUMENT_NAMES:
                continue

            if argument.annotation is not None:
                continue

            violation = Violation(
                path,
                argument.lineno,
                "PY-01",
                f"Parameter '{argument.arg}' of '{node.name}' has no type annotation.",
            )
            violations.append(violation)
    return violations


def check_none_returns(path: Path, tree: ast.Module) -> list[Violation]:
    """
    Check the -> None, return None, and trailing return rules.
    """
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if not isinstance(node, FUNCTION_NODE_TYPES):
            continue

        if is_none_constant(node.returns):
            violation = Violation(
                path,
                node.lineno,
                "PY-02",
                f"'{node.name}' is annotated '-> None'; omit the return annotation.",
            )
            violations.append(violation)

        allows_none = annotation_allows_none(node.returns)
        is_none_annotation = is_none_constant(node.returns)
        may_return_none_value = allows_none and not is_none_annotation
        for own_node in iter_own_body_nodes(node):
            if not isinstance(own_node, ast.Return):
                continue

            if not is_none_constant(own_node.value):
                continue

            if may_return_none_value:
                continue

            violation = Violation(
                path,
                own_node.lineno,
                "PY-03",
                "Write a bare 'return', never 'return None'.",
            )
            violations.append(violation)
        if is_trailing_bare_return(node.body[-1]):
            last_statement = node.body[-1]
            violation = Violation(
                path,
                last_statement.lineno,
                "PY-04",
                f"Trailing bare 'return' at the end of '{node.name}' is not needed.",
            )
            violations.append(violation)
    return violations


def check_module_header(path: Path, tree: ast.Module) -> list[Violation]:
    """
    Check the page docstring with :author: and :date:.
    """
    docstring_node = get_docstring_node(tree)
    if docstring_node is None or docstring_node.lineno != 1:
        violation = Violation(
            path,
            1,
            "PY-07",
            "File must start with the page docstring (description, :author:, :date:).",
        )
        return [violation]

    violations: list[Violation] = []
    if AUTHOR_PATTERN.search(str(docstring_node.value)) is None:
        violation = Violation(
            path,
            1,
            "PY-07",
            "Missing ':author: NAME'.",
        )
        violations.append(violation)

    if DATE_PATTERN.search(str(docstring_node.value)) is None:
        violation = Violation(
            path,
            1,
            "PY-07",
            "Missing ':date: DD/MM/YY'.",
        )
        violations.append(violation)

    return violations


def check_docstring_layout(
    path: Path,
    docstring_node: ast.Constant,
    lines: list[str],
) -> list[Violation]:
    """
    Check that a docstring's quotes sit on their own lines and its fields are contiguous.

    :param path: The file being checked.
    :param docstring_node: The docstring's string constant.
    :param lines: The file's source lines.
    :return: The layout violations of this docstring.
    """
    violations: list[Violation] = []
    end_line = docstring_node.end_lineno or docstring_node.lineno
    opening_line = lines[docstring_node.lineno - 1].strip()
    closing_line = lines[end_line - 1].strip()
    if opening_line not in DOCSTRING_QUOTE_LINES or closing_line != '"""':
        violation = Violation(
            path,
            docstring_node.lineno,
            "PY-14",
            'Docstring opening and closing """ must each be on their own line.',
        )
        violations.append(violation)

    docstring_lines = str(docstring_node.value).splitlines()
    field_indexes = [
        index
        for index, docstring_line in enumerate(docstring_lines)
        if is_docstring_field(docstring_line)
    ]
    if len(field_indexes) < 2:
        return violations

    lines_between_fields = docstring_lines[field_indexes[0]:field_indexes[-1]]
    if any(
        docstring_line.strip() == ""
        for docstring_line in lines_between_fields
    ):
        violation = Violation(
            path,
            docstring_node.lineno,
            "PY-15",
            "No blank lines allowed between :param / :return / :raises fields.",
        )
        violations.append(violation)

    return violations


def check_docstrings(path: Path, tree: ast.Module, lines: list[str]) -> list[Violation]:
    """
    Check the layout of every docstring in the module.
    """
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if not isinstance(node, DOCSTRING_OWNER_NODE_TYPES):
            continue

        docstring_node = get_docstring_node(node)
        if docstring_node is None:
            continue

        if is_init_method(node):
            violation = Violation(
                path,
                docstring_node.lineno,
                "PY-16",
                "'__init__' must not have a docstring.",
            )
            violations.append(violation)

        violations += check_docstring_layout(
            path,
            docstring_node,
            lines,
        )
    return violations


def find_docstring_end_line(tree: ast.Module) -> int | None:
    """
    Return the last line of the page docstring.
    """
    docstring_node = get_docstring_node(tree)
    if docstring_node is None or docstring_node.lineno != 1:
        return None

    return docstring_node.end_lineno


def check_banner_spacing(
    path: Path,
    lines: list[str],
    index: int,
    section_name: str,
    docstring_end_line: int | None,
) -> list[Violation]:
    """
    Check the blank lines around one well-formed section banner.

    :param path: The file being checked.
    :param lines: The file's source lines.
    :param index: The 0-based index of the banner line.
    :param section_name: The banner's section name.
    :param docstring_end_line: The page docstring's last line, when the file has one.
    :return: The spacing violations of this banner.
    """
    violations: list[Violation] = []
    line_number = index + 1
    if section_name == IMPORTS_BANNER_NAME:
        rule_id = "PY-09"
        if docstring_end_line is not None and line_number != docstring_end_line + 1:
            violation = Violation(
                path,
                line_number,
                rule_id,
                "Imports banner must be on the line right after the page docstring's closing quotes.",
            )
            violations.append(violation)
    else:
        rule_id = "PY-10" if section_name == CONSTS_BANNER_NAME else "PY-11"
        actual_above = count_blank_lines_above(lines, index)
        if actual_above != BLANK_LINES_ABOVE_BANNER:
            violation = Violation(
                path,
                line_number,
                rule_id,
                f"'{section_name}' banner needs exactly 1 blank line above (found {actual_above}).",
            )
            violations.append(violation)

    expected_below = BLANK_LINES_BELOW_BANNER.get(
        section_name,
        DEFAULT_BLANK_LINES_BELOW_BANNER,
    )
    actual_below = count_blank_lines_below(lines, index)
    if actual_below != expected_below:
        violation = Violation(
            path,
            line_number,
            rule_id,
            f"'{section_name}' banner needs exactly {expected_below} blank line(s) below (found {actual_below}).",
        )
        violations.append(violation)

    return violations


def is_non_string_constant(node: ast.expr) -> bool:
    """
    Check whether a node is a constant that isn't a string.
    """
    if not isinstance(node, ast.Constant):
        return False

    return not isinstance(node.value, str)


def get_string_literal_lines(tree: ast.Module) -> set[int]:
    """
    List the line numbers that lie inside string literals.

    :param tree: The parsed module.
    :return: Every line number covered by a string constant or f-string.
    """
    string_lines: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Constant, ast.JoinedStr)):
            continue

        if is_non_string_constant(node):
            continue

        last_line = node.end_lineno or node.lineno
        string_lines.update(range(node.lineno, last_line + 1))

    return string_lines


def find_banner_line_indexes(tree: ast.Module, lines: list[str]) -> list[int]:
    """
    Find the indexes of banner-like comment lines outside string literals.

    :param tree: The parsed module.
    :param lines: The file's source lines.
    :return: The 0-based indexes of lines that look like section banners.
    """
    string_lines = get_string_literal_lines(tree)
    return [
        index
        for index, line in enumerate(lines)
        if BANNER_LIKE_PATTERN.match(line) is not None
        and index + 1 not in string_lines
    ]


def check_banners(path: Path, tree: ast.Module, lines: list[str]) -> list[Violation]:
    """
    Check the format and spacing of every section banner.
    """
    violations: list[Violation] = []
    docstring_end_line = find_docstring_end_line(tree)
    for index in find_banner_line_indexes(tree, lines):
        line = lines[index]
        banner_match = BANNER_PATTERN.match(line)
        if banner_match is None:
            violation = Violation(
                path,
                index + 1,
                "PY-08",
                "Section banner must be exactly '# ----- Name ----- #' with a capitalized name.",
            )
            violations.append(violation)
            continue

        violations += check_banner_spacing(
            path,
            lines,
            index,
            banner_match.group(1),
            docstring_end_line,
        )
    return violations


def check_dunder_all(path: Path, tree: ast.Module) -> list[Violation]:
    """
    Check that the module doesn't define __all__.
    """
    violations: list[Violation] = []
    for node in tree.body:
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            targets = [node.target]

        for target in targets:
            if get_target_name(target) == "__all__":
                violation = Violation(
                    path,
                    node.lineno,
                    "PY-13",
                    "Do not define '__all__' in application packages.",
                )
                violations.append(violation)
    return violations


def is_exception_base(base: ast.expr) -> bool:
    """
    Check whether a base class is an exception.
    """
    base_name = get_called_name(base)
    if base_name is None:
        return False

    is_builtin = base_name in BUILTIN_EXCEPTION_NAMES
    return is_builtin or base_name.endswith(EXCEPTION_NAME_SUFFIXES)


def check_exceptions(path: Path, tree: ast.Module) -> list[Violation]:
    """
    Check the custom exception rules.
    """
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise) and node.exc is not None:
            raised_name = get_called_name(node.exc)
            if raised_name is not None and raised_name in BUILTIN_EXCEPTION_NAMES:
                violation = Violation(
                    path,
                    node.lineno,
                    "PY-25",
                    f"Do not raise builtin '{raised_name}'; raise a custom domain exception.",
                )
                violations.append(violation)

        if not isinstance(node, ast.ClassDef):
            continue

        if node.name.endswith("Error"):
            continue

        if any(
            is_exception_base(base)
            for base in node.bases
        ):
            violation = Violation(
                path,
                node.lineno,
                "PY-26",
                f"Exception class '{node.name}' must end with 'Error'.",
            )
            violations.append(violation)
    return violations


def is_inside_f_string(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    """
    Check whether a node is part of an f-string.
    """
    current = parents.get(node)
    while current is not None:
        if isinstance(current, ast.JoinedStr):
            return True

        current = parents.get(current)
    return False


def is_argument_of_call_on_same_line(node: ast.Call, parents: dict[ast.AST, ast.AST]) -> bool:
    """
    Check whether the call is an argument of an enclosing call that starts on the same line.

    :param node: The call being checked.
    :param parents: Child-to-parent node map of the module.
    :return: Whether the enclosing call owns this line, so only it has to be split.
    """
    child: ast.AST = node
    current = parents.get(node)
    while current is not None:
        owner_line = get_argument_owner_line(current, child)
        if owner_line == node.lineno:
            return True

        child = current
        current = parents.get(current)
    return False


def get_call_arguments(node: ast.Call) -> list[ast.expr | ast.keyword]:
    """
    Return a call's arguments in source order.
    """
    arguments: list[ast.expr | ast.keyword] = [
        *node.args,
        *node.keywords,
    ]
    return sorted(
        arguments,
        key=lambda argument: (argument.lineno, argument.col_offset),
    )


def measure_single_line_length(node: ast.Call, line_bytes: list[bytes]) -> int:
    """
    Measure the line a call would make if it were written on a single line.

    :param node: The call being measured.
    :param line_bytes: The file's lines encoded as UTF-8.
    :return: The length of that line, including indentation and the code around the call.
    """
    end_line = node.end_lineno or node.lineno
    end_column = node.end_col_offset or 0
    start_line_bytes = line_bytes[node.lineno - 1]
    end_line_bytes = line_bytes[end_line - 1]
    text_before = start_line_bytes[:node.col_offset].decode("utf-8")
    text_after = end_line_bytes[end_column:].decode("utf-8").rstrip()
    call_length = len(ast.unparse(node))
    return len(text_before) + call_length + len(text_after)


def call_requires_multiline(
    node: ast.Call,
    arguments: list[ast.expr | ast.keyword],
    line_bytes: list[bytes],
) -> bool:
    """
    Check whether a call must have one argument per line.
    """
    if len(arguments) >= MULTILINE_CALL_MIN_ARGUMENTS:
        return True

    line_length = measure_single_line_length(node, line_bytes)
    return line_length >= MULTILINE_CALL_MIN_LINE_LENGTH


def is_properly_exploded(
    node: ast.Call,
    arguments: list[ast.expr | ast.keyword],
    line_bytes: list[bytes],
) -> bool:
    """
    Check whether every argument of a call sits on its own line and ends with a trailing comma.

    :param node: The call being checked.
    :param arguments: The call's arguments in source order.
    :param line_bytes: The file's lines encoded as UTF-8.
    :return: Whether the call is laid out one argument per line with a trailing comma.
    """
    previous_end_line = node.func.end_lineno
    for argument in arguments:
        if previous_end_line is None or argument.lineno <= previous_end_line:
            return False

        previous_end_line = argument.end_lineno
    last_argument = arguments[-1]
    if last_argument.end_lineno is None or last_argument.end_col_offset is None:
        return False

    if node.end_lineno is None or node.end_col_offset is None:
        return False

    closing_text = read_source_segment(
        line_bytes,
        (last_argument.end_lineno, last_argument.end_col_offset),
        (node.end_lineno, node.end_col_offset),
    )
    return "," in closing_text


def check_multiline_calls(
    path: Path,
    tree: ast.Module,
    line_bytes: list[bytes],
    parents: dict[ast.AST, ast.AST],
) -> list[Violation]:
    """
    Check that long calls have one argument per line.
    """
    violations: list[Violation] = []
    reported_lines: set[int] = set()
    calls = sorted(
        (
            node
            for node in ast.walk(tree)
            if is_call(node)
        ),
        key=lambda call: (call.lineno, call.col_offset),
    )
    for node in calls:
        if is_inside_f_string(node, parents):
            continue

        arguments = get_call_arguments(node)
        if len(arguments) == 0:
            continue

        if is_single_generator_call(node):
            continue

        if not call_requires_multiline(
            node,
            arguments,
            line_bytes,
        ):
            continue

        if is_argument_of_call_on_same_line(node, parents):
            continue

        if node.lineno in reported_lines:
            continue

        if is_properly_exploded(
            node,
            arguments,
            line_bytes,
        ):
            continue

        reported_lines.add(node.lineno)
        violation = Violation(
            path,
            node.lineno,
            "PY-24",
            f"'{get_called_name(node) or 'call'}(...)' has 3+ arguments or makes a 70+ character line: "
            "put each argument on its own line and add a trailing comma.",
        )
        violations.append(violation)
    return violations


def check_class_docstring_spacing(
    path: Path,
    tree: ast.Module,
    lines: list[str],
) -> list[Violation]:
    """
    Check that no blank line follows a class docstring.
    """
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or len(node.body) < 2:
            continue

        docstring_node = get_docstring_node(node)
        if docstring_node is None or docstring_node.end_lineno is None:
            continue

        if lines[docstring_node.end_lineno].strip() != "":
            continue

        violation = Violation(
            path,
            docstring_node.end_lineno + 1,
            "PY-29",
            f"No blank line between the docstring of '{node.name}' and its body.",
        )
        violations.append(violation)
    return violations


def is_table_model(node: ast.ClassDef) -> bool:
    """
    Check whether a class is a table model (table=True).
    """
    for keyword in node.keywords:
        if keyword.arg != "table":
            continue

        if not isinstance(keyword.value, ast.Constant):
            continue

        if keyword.value.value is True:
            return True
    return False


def get_assigned_name(statement: ast.stmt) -> str | None:
    """
    Return the name a statement assigns to, when it's a single plain name.
    """
    if isinstance(statement, ast.Assign):
        if len(statement.targets) != 1:
            return None

        return get_target_name(statement.targets[0])

    if not isinstance(statement, ast.AnnAssign):
        return None

    if isinstance(statement.target, ast.Name):
        return statement.target.id

    return None


def check_table_model_layout(path: Path, tree: ast.Module) -> list[Violation]:
    """
    Check that table models put __tablename__ first and __table_args__ last.

    :param path: The file being checked.
    :param tree: The parsed module.
    :return: The layout violations of every table model in the module.
    """
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        if not is_table_model(node):
            continue

        has_docstring = get_docstring_node(node) is not None
        body = node.body[1:] if has_docstring else node.body
        names = [
            get_assigned_name(statement)
            for statement in body
        ]
        if TABLE_NAME_ATTRIBUTE in names and names[0] != TABLE_NAME_ATTRIBUTE:
            violation = Violation(
                path,
                body[names.index(TABLE_NAME_ATTRIBUTE)].lineno,
                "PY-30",
                f"'{TABLE_NAME_ATTRIBUTE}' must come right after the docstring of '{node.name}'.",
            )
            violations.append(violation)

        if TABLE_ARGS_ATTRIBUTE in names and names[-1] != TABLE_ARGS_ATTRIBUTE:
            violation = Violation(
                path,
                body[names.index(TABLE_ARGS_ATTRIBUTE)].lineno,
                "PY-31",
                f"'{TABLE_ARGS_ATTRIBUTE}' must be the last statement of '{node.name}'.",
            )
            violations.append(violation)
    return violations


def iter_statement_blocks(tree: ast.Module) -> list[list[ast.stmt]]:
    """
    List every block of statements in the module.
    """
    blocks: list[list[ast.stmt]] = []
    for node in ast.walk(tree):
        for field_name in ("body", "orelse", "finalbody"):
            block = getattr(
                node,
                field_name,
                None,
            )
            if is_statement_block(block):
                blocks.append(block)
    return blocks


def check_blank_line_after_if(
    path: Path,
    tree: ast.Module,
    lines: list[str],
) -> list[Violation]:
    """
    Check that a blank line follows every if block that has code after it.
    """
    violations: list[Violation] = []
    for block in iter_statement_blocks(tree):
        for statement, next_statement in itertools.pairwise(block):
            if not isinstance(statement, ast.If):
                continue

            if statement.end_lineno is None:
                continue

            if next_statement.lineno <= statement.end_lineno:
                continue

            if lines[statement.end_lineno].strip() == "":
                continue

            violation = Violation(
                path,
                statement.end_lineno + 1,
                "PY-32",
                "Leave one blank line after an if block when more code follows it.",
            )
            violations.append(violation)
    return violations


def check_function_docstrings(path: Path, tree: ast.Module) -> list[Violation]:
    """
    Check that every function and method has a docstring (except __init__).

    :param path: The file being checked.
    :param tree: The parsed module.
    :return: One violation per function without a docstring.
    """
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if not isinstance(node, FUNCTION_NODE_TYPES):
            continue

        if node.name == "__init__":
            continue

        if get_docstring_node(node) is not None:
            continue

        violation = Violation(
            path,
            node.lineno,
            "PY-35",
            f"'{node.name}' needs a docstring.",
        )
        violations.append(violation)
    return violations


def is_short_name(name: str) -> bool:
    """
    Check whether a name is a single letter or a known abbreviation.
    """
    if name in SHORT_NAME_ALLOWLIST:
        return False

    return len(name) == 1 or name in ABBREVIATED_NAMES


def iter_bound_names(node: ast.AST) -> list[tuple[str, int]]:
    """
    List the names a node binds, with their lines.

    :param node: Any AST node.
    :return: The (name, line) pairs of the variables the node creates.
    """
    bound_names: list[tuple[str, int]] = []
    targets: list[ast.AST] = []
    if isinstance(node, ast.Assign):
        targets = list(node.targets)
    elif isinstance(node, SINGLE_TARGET_NODE_TYPES):
        targets = [node.target]
    elif isinstance(node, ast.withitem):
        if node.optional_vars is not None:
            targets = [node.optional_vars]

    elif isinstance(node, ast.ExceptHandler):
        if node.name is not None:
            bound_names.append((node.name, node.lineno))

    elif isinstance(node, ast.arg):
        bound_names.append((node.arg, node.lineno))

    for target in targets:
        for target_node in ast.walk(target):
            if not isinstance(target_node, ast.Name):
                continue

            bound_names.append((target_node.id, target_node.lineno))

    return bound_names


def check_short_names(path: Path, tree: ast.Module) -> list[Violation]:
    """
    Check that variables, parameters, and except names aren't abbreviated.

    :param path: The file being checked.
    :param tree: The parsed module.
    :return: One violation per short or abbreviated name.
    """
    violations: list[Violation] = []
    reported: set[tuple[str, int]] = set()
    for node in ast.walk(tree):
        for name, line in iter_bound_names(node):
            if not is_short_name(name) or (name, line) in reported:
                continue

            reported.add((name, line))
            violation = Violation(
                path,
                line,
                "PY-36",
                f"'{name}' is too short or abbreviated: write the full word.",
            )
            violations.append(violation)
    return violations


def contains_depends_call(node: ast.AST) -> bool:
    """
    Check whether an expression contains a FastAPI Depends(...) call.
    """
    for child in ast.walk(node):
        if is_call(child) and get_called_name(child) == DEPENDS_NAME:
            return True

    return False


def check_dependency_constants(
    path: Path,
    tree: ast.Module,
) -> list[Violation]:
    """
    Check that no module or class constant stores a dependency.

    :param path: The file being checked.
    :param tree: The parsed module.
    :return: One violation per constant or alias holding Depends(...).
    """
    violations: list[Violation] = []
    containers: list[ast.Module | ast.ClassDef] = [tree]
    containers.extend(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
    )
    for container in containers:
        for statement in container.body:
            if not isinstance(statement, ASSIGNMENT_NODE_TYPES):
                continue

            value = statement.value
            if value is None or not contains_depends_call(value):
                continue

            violation = Violation(
                path,
                statement.lineno,
                "PY-37",
                "Don't store a dependency in a constant: call Depends(...) "
                "in each endpoint's signature.",
            )
            violations.append(violation)
    return violations


def get_comprehension_parts(node: ast.expr) -> list[tuple[int, int]]:
    """
    List the (first line, last line) of each part of a comprehension.

    :param node: A list, set, or dict comprehension or a generator expression.
    :return: The expression, each for clause, and each if clause, in order.
    """
    parts: list[tuple[int, int]] = []
    if isinstance(node, ast.DictComp):
        value_end = node.value.end_lineno or 0
        parts.append((node.key.lineno, value_end))
    elif isinstance(node, SINGLE_ELEMENT_COMPREHENSION_TYPES):
        element_end = node.elt.end_lineno or 0
        parts.append((node.elt.lineno, element_end))

    generators: list[ast.comprehension] = getattr(
        node,
        "generators",
        [],
    )
    for generator in generators:
        iterable_end = generator.iter.end_lineno or 0
        parts.append((generator.target.lineno, iterable_end))
        for condition in generator.ifs:
            condition_end = condition.end_lineno or 0
            parts.append((condition.lineno, condition_end))

    return parts


def is_comprehension_exploded(node: ast.expr) -> bool:
    """
    Check whether every part of a comprehension starts on a new line.
    """
    previous_end = node.lineno
    for first_line, last_line in get_comprehension_parts(node):
        if first_line <= previous_end:
            return False

        previous_end = last_line

    return (node.end_lineno or 0) > previous_end


def check_comprehension_layout(
    path: Path,
    tree: ast.Module,
    parents: dict[ast.AST, ast.AST],
) -> list[Violation]:
    """
    Check that comprehensions put each part on its own line.

    :param path: The file being checked.
    :param tree: The parsed module.
    :param parents: Child-to-parent node map of the module.
    :return: One violation per comprehension written on too few lines.
    """
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if not isinstance(node, COMPREHENSION_NODE_TYPES):
            continue

        if is_inside_f_string(node, parents):
            continue

        if is_comprehension_exploded(node):
            continue

        violation = Violation(
            path,
            node.lineno,
            "PY-38",
            "Put the expression, each 'for', each 'if', and the closing "
            "bracket of a comprehension on their own lines.",
        )
        violations.append(violation)
    return violations


def check_empty_classes(path: Path, tree: ast.Module) -> list[Violation]:
    """
    Check that a class with only a docstring ends with pass.

    :param path: The file being checked.
    :param tree: The parsed module.
    :return: One violation per class whose body is only a docstring.
    """
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        if len(node.body) != 1:
            continue

        if get_docstring_node(node) is None:
            continue

        violation = Violation(
            path,
            node.lineno,
            "PY-39",
            f"Class '{node.name}' has only a docstring: add 'pass'.",
        )
        violations.append(violation)
    return violations


def get_session_method_call(node: ast.AST) -> str | None:
    """
    Return the method name when a node calls a method on a session.

    :param node: Any AST node.
    :return: The called method's name, when it's called on a session.
    """
    if not is_call(node) or not isinstance(node.func, ast.Attribute):
        return None

    receiver_name = get_called_name(node.func.value)
    if receiver_name is None:
        return None

    if SESSION_NAME_PART not in receiver_name.lower():
        return None

    return node.func.attr


def check_session_rollback(path: Path, tree: ast.Module) -> list[Violation]:
    """
    Check that no code rolls back through the session.

    :param path: The file being checked.
    :param tree: The parsed module.
    :return: One violation per session.rollback() call.
    """
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if not is_call(node):
            continue

        if get_session_method_call(node) != ROLLBACK_METHOD:
            continue

        violation = Violation(
            path,
            node.lineno,
            "PY-40",
            "Don't call session.rollback(): start a transaction and "
            "call transaction.rollback().",
        )
        violations.append(violation)
    return violations


def check_test_file_header(
    path: Path,
    tree: ast.Module,
    lines: list[str],
) -> list[Violation]:
    """
    Check that a test file has no page docstring and no section banners.

    :param path: The test file being checked.
    :param tree: The parsed module.
    :param lines: The file's source lines.
    :return: The header and banner violations of the test file.
    """
    violations: list[Violation] = []
    if get_docstring_node(tree) is not None:
        violation = Violation(
            path,
            1,
            "TS-27",
            "Test files have no page docstring.",
        )
        violations.append(violation)

    for index in find_banner_line_indexes(tree, lines):
        violation = Violation(
            path,
            index + 1,
            "TS-27",
            "Test files have no section banners.",
        )
        violations.append(violation)
    return violations


def check_session_writes_in_tests(
    path: Path,
    tree: ast.Module,
) -> list[Violation]:
    """
    Check that test bodies don't create or change data through the session.

    :param path: The test file being checked.
    :param tree: The parsed module.
    :return: One violation per session write in the test file.
    """
    violations: list[Violation] = []
    if path.name == CONFTEST_FILE_NAME:
        return violations

    for node in ast.walk(tree):
        if not is_call(node):
            continue

        method_name = get_session_method_call(node)
        if method_name not in SESSION_WRITE_METHODS:
            continue

        violation = Violation(
            path,
            node.lineno,
            "TS-28",
            f"Don't call session.{method_name}() in a test: create data "
            "with conftest fixtures or the app's own functions.",
        )
        violations.append(violation)
    return violations


def get_description_line(docstring: str) -> str | None:
    """
    Return the first non-empty line of a docstring.

    :param docstring: The docstring's text.
    :return: The description line, when the docstring has one.
    """
    for docstring_line in docstring.splitlines():
        if docstring_line.strip() != "":
            return docstring_line.strip()

    return None


def to_imperative(word: str) -> str:
    """
    Turn a third-person verb such as 'Checks' into its imperative form.
    """
    lowered_word = word.lower()
    if lowered_word.endswith("ies"):
        return word[:-3] + "y"

    has_es_ending = lowered_word.endswith(ES_PLURAL_ENDINGS)
    if has_es_ending:
        return word[:-2]

    return word[:-1]


def is_third_person_verb(word: str) -> bool:
    """
    Check whether a word reads like a third-person verb ('Locks', 'Returns').

    :param word: The first word of a description.
    :return: Whether the word ends in 's' the way a third-person verb does.
    """
    lowered_word = word.lower()
    if not lowered_word.endswith(THIRD_PERSON_SUFFIX):
        return False

    return not lowered_word.endswith(NON_THIRD_PERSON_ENDINGS)


def check_docstring_mood(path: Path, tree: ast.Module) -> list[Violation]:
    """
    Check that function descriptions are written in the imperative mood.

    :param path: The file being checked.
    :param tree: The parsed module.
    :return: One violation per description that starts with a third-person verb.
    """
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if not isinstance(node, FUNCTION_NODE_TYPES):
            continue

        docstring_node = get_docstring_node(node)
        if docstring_node is None:
            continue

        docstring = str(docstring_node.value)
        description_line = get_description_line(docstring)
        if description_line is None:
            continue

        word_match = FIRST_WORD_PATTERN.match(description_line)
        if word_match is None:
            continue

        first_word = word_match.group(1)
        if not is_third_person_verb(first_word):
            continue

        violation = Violation(
            path,
            docstring_node.lineno,
            "PY-41",
            f"Write the description of '{node.name}' in the imperative mood: "
            f"'{to_imperative(first_word)}', not '{first_word}'.",
        )
        violations.append(violation)
    return violations


def check_boolean_return_docs(path: Path, tree: ast.Module) -> list[Violation]:
    """
    Check that boolean returns are described by what they mean.

    :param path: The file being checked.
    :param tree: The parsed module.
    :return: One violation per ':return:' line that starts with True or False.
    """
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if not isinstance(node, FUNCTION_NODE_TYPES):
            continue

        docstring_node = get_docstring_node(node)
        if docstring_node is None:
            continue

        for docstring_line in str(docstring_node.value).splitlines():
            field_line = docstring_line.strip()
            if not field_line.startswith(RETURN_FIELD_PREFIX):
                continue

            field_text = field_line.removeprefix(RETURN_FIELD_PREFIX)
            return_text = field_text.strip().lower()
            is_boolean_return = return_text.startswith(
                BOOLEAN_RETURN_WORDS,
            )
            if not is_boolean_return:
                continue

            violation = Violation(
                path,
                docstring_node.lineno,
                "PY-42",
                f"Describe the return of '{node.name}' by what it means "
                "('Whether ...'), not 'True when ..., False when ...'.",
            )
            violations.append(violation)
    return violations


def check_string_enums(path: Path, tree: ast.Module) -> list[Violation]:
    """
    Check that string enums inherit from StrEnum.

    :param path: The file being checked.
    :param tree: The parsed module.
    :return: One violation per class that inherits from both str and Enum.
    """
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        base_names = {
            get_called_name(base)
            for base in node.bases
        }
        is_str_enum = STR_BASE_NAME in base_names and ENUM_BASE_NAME in base_names
        if not is_str_enum:
            continue

        violation = Violation(
            path,
            node.lineno,
            "PY-43",
            f"'{node.name}' holds strings: inherit from StrEnum, not str and Enum.",
        )
        violations.append(violation)
    return violations


def is_inside_annotation(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    """
    Check whether a node is part of a subscript such as Callable[[int, str], bool].

    :param node: The node to check.
    :param parents: The parent of every node in the module.
    :return: Whether the node is inside the brackets of a subscript.
    """
    parent = parents.get(node)
    while parent is not None:
        if isinstance(parent, ast.Subscript):
            return True

        if isinstance(parent, ast.stmt):
            return False

        parent = parents.get(parent)
    return False


def is_small_collection(node: ast.List | ast.Set) -> bool:
    """
    Check whether a list or set literal is small enough to stay on one line.

    :param node: The list or set literal.
    :return: Whether the literal is on one line and at most the small length.
    """
    if node.end_lineno != node.lineno or node.end_col_offset is None:
        return False

    literal_length = node.end_col_offset - node.col_offset
    return literal_length <= SMALL_COLLECTION_MAX_LENGTH


def is_collection_exploded(node: ast.List | ast.Set) -> bool:
    """
    Check whether every item of a list or set literal is on its own line.

    :param node: The list or set literal.
    :return: Whether the brackets and every item are on separate lines.
    """
    item_lines = [
        item.lineno
        for item in node.elts
    ]
    last_item_end_line = node.elts[-1].end_lineno
    if item_lines[0] == node.lineno or last_item_end_line is None:
        return False

    if node.end_lineno is None or last_item_end_line >= node.end_lineno:
        return False

    return len(set(item_lines)) == len(item_lines)


def check_collection_literals(
    path: Path,
    tree: ast.Module,
    parents: dict[ast.AST, ast.AST],
) -> list[Violation]:
    """
    Check that list and set literals put each of their items on its own line.

    :param path: The file being checked.
    :param tree: The parsed module.
    :param parents: The parent of every node in the module.
    :return: One violation per list or set literal with items sharing a line.
    """
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if not isinstance(node, COLLECTION_LITERAL_TYPES):
            continue

        if len(node.elts) < 2 or is_inside_annotation(node, parents):
            continue

        if is_collection_exploded(node) or is_small_collection(node):
            continue

        violation = Violation(
            path,
            node.lineno,
            "PY-44",
            "Put each item of this list or set on its own line, with the "
            "brackets on their own lines and a trailing comma.",
        )
        violations.append(violation)
    return violations


def check_environment_fixture(path: Path, tree: ast.Module) -> list[Violation]:
    """
    Check that test data is created only by the env fixture.

    :param path: The test file being checked.
    :param tree: The parsed module.
    :return: One violation per conftest session write outside the env fixture.
    """
    violations: list[Violation] = []
    if path.name != CONFTEST_FILE_NAME:
        return violations

    for statement in tree.body:
        if not isinstance(statement, FUNCTION_NODE_TYPES):
            continue

        if statement.name == ENVIRONMENT_FIXTURE_NAME:
            continue

        for node in ast.walk(statement):
            if not is_call(node):
                continue

            method_name = get_session_method_call(node)
            if method_name not in SESSION_WRITE_METHODS:
                continue

            violation = Violation(
                path,
                node.lineno,
                "TS-30",
                f"Only the '{ENVIRONMENT_FIXTURE_NAME}' fixture creates test data: "
                f"move this session.{method_name}() into it.",
            )
            violations.append(violation)
    return violations


def check_python_file(path: Path) -> list[Violation]:
    """
    Run every convention check on one Python file.

    :param path: The file to check.
    :return: All violations found, sorted by line.
    """
    raw_source = path.read_bytes()
    source = raw_source.decode("utf-8-sig")
    if source.strip() == "" or is_migration_file(path):
        return []

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as syntax_error:
        violation = Violation(
            path,
            syntax_error.lineno or 1,
            "PY-SYNTAX",
            f"Syntax error: {syntax_error.msg}",
        )
        return [violation]
    lines = source.splitlines()
    line_bytes = [
        line.encode("utf-8")
        for line in lines
    ]
    parents = build_parent_map(tree)
    violations = check_encoding(path, raw_source)
    violations += check_none_returns(path, tree)
    violations += check_docstrings(
        path,
        tree,
        lines,
    )
    violations += check_dunder_all(path, tree)
    violations += check_exceptions(path, tree)
    violations += check_class_docstring_spacing(
        path,
        tree,
        lines,
    )
    violations += check_table_model_layout(path, tree)
    violations += check_blank_line_after_if(
        path,
        tree,
        lines,
    )
    violations += check_short_names(path, tree)
    violations += check_dependency_constants(path, tree)
    violations += check_comprehension_layout(
        path,
        tree,
        parents,
    )
    violations += check_empty_classes(path, tree)
    violations += check_session_rollback(path, tree)
    violations += check_string_enums(path, tree)
    violations += check_collection_literals(
        path,
        tree,
        parents,
    )
    if is_test_file(path):
        violations += check_test_file_header(
            path,
            tree,
            lines,
        )
        violations += check_session_writes_in_tests(path, tree)
        violations += check_environment_fixture(path, tree)

    if not is_test_file(path):
        violations += check_function_docstrings(path, tree)
        violations += check_docstring_mood(path, tree)
        violations += check_boolean_return_docs(path, tree)
        violations += check_parameter_annotations(
            path,
            tree,
            parents,
        )
        violations += check_module_header(path, tree)
        violations += check_banners(
            path,
            tree,
            lines,
        )
        violations += check_multiline_calls(
            path,
            tree,
            line_bytes,
            parents,
        )

    return sorted(violations, key=lambda violation: violation.line)


def collect_python_files(raw_paths: list[str]) -> list[Path]:
    """
    Collect the Python files in the given files and directories.
    """
    python_files: list[Path] = []
    for raw_path in raw_paths:
        path = Path(raw_path)
        if path.is_dir():
            python_files.extend(sorted(path.rglob("*.py")))
        elif path.suffix == ".py" and path.is_file():
            python_files.append(path)
    return python_files


def write_utf8(text: str):
    """
    Write text to stdout as UTF-8.
    """
    sys.stdout.buffer.write(text.encode("utf-8"))
    sys.stdout.flush()


def main() -> int:
    """
    Check the given paths and print every violation.
    """
    parser = argparse.ArgumentParser(
        description="Check Python files against the house conventions.",
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Python files or directories to check.",
    )
    parsed_arguments = parser.parse_args()
    violations: list[Violation] = []
    for python_file in collect_python_files(parsed_arguments.paths):
        violations += check_python_file(python_file)
    if len(violations) == 0:
        return 0

    for violation in violations:
        write_utf8(violation.format_for_output() + "\n")
    write_utf8(f"{len(violations)} convention violation(s).\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
