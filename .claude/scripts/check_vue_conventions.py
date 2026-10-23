"""
Check Vue and TypeScript files against the house conventions that eslint doesn't cover.

:author: Noam
:date: 23/10/26
"""
# ----- Imports ----- #

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from changed_lines import get_changed_lines

# ----- Consts ----- #

FRONTEND_SUFFIXES = (
    ".vue",
    ".ts",
    ".tsx",
)
SKIPPED_DIRECTORY_NAMES = frozenset(
    {
        "node_modules",
        "dist",
        ".git",
    },
)
THEME_FILE_NAMES = frozenset(
    {
        "vuetify.ts",
        "vuetify.js",
    },
)
TEST_FILE_PATTERN = re.compile(r"\.(?:spec|test)\.tsx?$")
STRUCTURE_RULE_IDS = frozenset(
    {
        "VU-05",
        "VU-27",
        "VU-32",
    },
)
BLOCK_PATTERN = re.compile(
    r"^<(template|script|style)\b([^>]*)>\n?(.*?)^</\1>",
    re.MULTILINE | re.DOTALL,
)
TEMPLATE_BINDING_PATTERN = re.compile(
    r"(?<![\w:-])(?:[:@#][\w.\[\]-]*|v-[\w-]+(?::[\w\[\]-]+)?(?:\.[\w-]+)*)\s*=\s*\"([^\"]*)\"",
)
TEMPLATE_INTERPOLATION_PATTERN = re.compile(
    r"\{\{(.*?)\}\}",
    re.DOTALL,
)
HTML_COMMENT_PATTERN = re.compile(
    r"<!--.*?-->",
    re.DOTALL,
)
CSS_COMMENT_PATTERN = re.compile(
    r"/\*.*?\*/",
    re.DOTALL,
)
STYLE_ATTRIBUTE_PATTERN = re.compile(
    r"(?<![\w-]):?style\s*=\s*\"([^\"]*)\"",
)
PALETTE_NAMES = (
    "red",
    "pink",
    "purple",
    "deep-purple",
    "indigo",
    "blue",
    "light-blue",
    "cyan",
    "teal",
    "green",
    "light-green",
    "lime",
    "yellow",
    "amber",
    "orange",
    "deep-orange",
    "brown",
    "blue-grey",
    "grey",
    "gray",
    "slate",
    "zinc",
    "neutral",
    "stone",
    "emerald",
    "sky",
    "violet",
    "fuchsia",
    "rose",
    "black",
    "white",
)
PALETTE_ALTERNATIVES = "|".join(PALETTE_NAMES)
COLOR_CLASS_PATTERN = re.compile(
    r"(?<![\w-])(?:text|bg|border|ring|fill|stroke|from|via|to|outline|decoration|divide|placeholder"
    r"|accent|caret|shadow)-(?:"
    + PALETTE_ALTERNATIVES
    + r")(?:-(?:lighten|darken|accent)-\d|-\d{2,3})?(?![\w-])",
)
COLOR_ATTRIBUTE_PATTERN = re.compile(
    r"(?<![\w-]):?(?:color|bg-color|base-color)\s*=\s*\"'?(?:"
    + PALETTE_ALTERNATIVES
    + r")(?:-(?:lighten|darken|accent)-\d)?'?\"",
)
CSS_COLOR_VALUE_PATTERN = re.compile(
    r"#[0-9a-fA-F]{3,8}\b|\b(?:rgb|rgba|hsl|hsla)\((?!\s*var\()",
)
CSS_NAMED_COLOR_PATTERN = re.compile(
    r"(?:color|background|background-color|border|border-color|fill|stroke|outline|outline-color)\s*:"
    r"[^;\"'}]*\b(?:red|blue|green|yellow|orange|purple|pink|brown|black|white|gray|grey)\b",
)
COLOR_STRING_PATTERN = re.compile(
    r"^\s*(?:#[0-9a-fA-F]{3,8}\s*$|(?:rgb|rgba|hsl|hsla)\((?!\s*var\())",
)
OPERATOR_RULES = (
    (
        re.compile(r"\?\?"),
        "VU-33",
        "Don't use ??: write the full === null / === undefined check.",
    ),
    (
        re.compile(r"\?\.(?!\d)"),
        "VU-33",
        "Don't use ?.: check for null or undefined with a full if first.",
    ),
    (
        re.compile(r"!!"),
        "VU-33",
        "Don't use !!: write the full check of what you mean.",
    ),
    (
        re.compile(
            r"(?:\|\||&&)\s*(?:['\"`\[{]|\d|null\b|undefined\b)",
        ),
        "VU-33",
        "Don't pick a value with || or &&: write a full if with the exact check.",
    ),
    (
        re.compile(r"\bvoid\s+(?:[A-Za-z_$][\w$.]*\s*\(|\()"),
        "VU-35",
        "Don't put void before a call: call it as it is, or await it.",
    ),
)
COMMENT_MESSAGE = "Remove the comment: frontend code has no comments."
COLOR_MESSAGE = "Hard-coded color: use a theme color from vuetify.ts (add a new theme key when none fits)."
EXPORT_MESSAGE = "A .vue file exports nothing: move it to src/utils/, src/models/, or its own module."
CONSTANT_IN_SETUP_MESSAGE = "Move the constant to the <script lang=\"ts\"> block."
SHORT_STRING_CONSTANT_MESSAGE = "This constant holds a string of 3 words or fewer: write the string inline where it's used."
LONG_INLINE_STRING_MESSAGE = "A string of more than 3 words is written inline: move it to a named constant."
INLINE_MACRO_TYPE_MESSAGE = "Don't write the type inside {macro}<...>(): declare interface {name} in <script lang=\"ts\">."
WRONG_MACRO_TYPE_MESSAGE = "Name the interface exactly {name} and use {macro}<{name}>()."
RUNTIME_MACRO_MESSAGE = "Use {macro}<{name}>() with interface {name}, not a runtime declaration."
INTERFACE_IN_SETUP_MESSAGE = "Declare {name} in the <script lang=\"ts\"> block, not in <script setup>."
MISSING_INTERFACE_MESSAGE = "{macro}<{name}>() is used, but <script lang=\"ts\"> has no interface {name}."
DESCRIPTION = "Check Vue and TypeScript files against the house conventions."
PATHS_HELP = "Files or directories to check."
SINCE_HELP = "Report only what the branch wrote since this git ref ('auto': the feature's base or the merge base)."
MACRO_INTERFACE_NAMES = (
    (
        "defineProps",
        "Props",
    ),
    (
        "defineEmits",
        "Emits",
    ),
)
SETUP_CONSTANT_PATTERN = re.compile(
    r"^const\s+[A-Z][A-Z0-9_]*\s*[:=]",
    re.MULTILINE,
)
EXPORT_PATTERN = re.compile(
    r"^\s*export\b",
    re.MULTILINE,
)
CONSTANT_VALUE_PREFIX_PATTERN = re.compile(
    r"\bconst\s+[A-Z][A-Z0-9_]*\s*(?::[^=\n]*)?=\s*$",
)
LAST_DECLARATION_PATTERN = re.compile(
    r"\b(?:const|let|var|function)\s+([A-Za-z_$][\w$]*)",
)
SETUP_ATTRIBUTE_PATTERN = re.compile(r"\bsetup\b")
UPPER_NAME_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
NON_NEWLINE_PATTERN = re.compile(r"[^\n]")
SHORT_STRING_MAX_WORDS = 3
DECLARATION_LOOKBACK_CHARACTERS = 2000

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


@dataclass(frozen=True)
class SourceBlock:
    """
    One top-level block of a single-file component, or the whole of a .ts file.
    """
    kind: str
    attributes: str
    text: str
    start_line: int

    def is_setup_script(self) -> bool:
        """
        Check whether the block is the <script setup> block.

        :return: Whether the block is a script with the setup attribute.
        """
        setup_match = SETUP_ATTRIBUTE_PATTERN.search(self.attributes)
        has_setup = setup_match is not None
        return self.kind == "script" and has_setup


@dataclass(frozen=True)
class StringLiteral:
    """
    A string literal found in script code.
    """
    start: int
    value: str
    is_template: bool


@dataclass(frozen=True)
class LexedCode:
    """
    Script code with string contents and comments blanked out, plus what was blanked.
    """
    code: str
    comment_offsets: list[int]
    strings: list[StringLiteral]

# ----- Functions ----- #


def line_of(text: str, offset: int) -> int:
    """
    Return the 1-based line of an offset in a text.
    """
    line_breaks = text.count(
        "\n",
        0,
        offset,
    )
    return line_breaks + 1


def blank_out(text: str) -> str:
    """
    Replace every character of a text with a space, keeping its line breaks.
    """
    return NON_NEWLINE_PATTERN.sub(" ", text)


def blank_match(text_match: re.Match[str]) -> str:
    """
    Blank out the text of a regex match.
    """
    return blank_out(text_match.group(0))


def find_string_end(text: str, start: int) -> int:
    """
    Find the offset just after the closing quote of a string literal.

    :param text: The code.
    :param start: The offset of the opening quote.
    :return: The offset after the closing quote, or the end of the line or text for an unclosed string.
    """
    quote = text[start]
    index = start + 1
    while index < len(text):
        character = text[index]
        if character == "\\":
            index += 2
            continue

        if character == quote:
            return index + 1

        if character == "\n" and quote != "`":
            return index

        index += 1
    return len(text)


def find_comment_end(text: str, start: int) -> int:
    """
    Find the offset just after a // or /* */ comment.

    :param text: The code.
    :param start: The offset of the comment's first slash.
    :return: The offset of the line break after a // comment, or the offset after the closing */.
    """
    if text[start + 1] == "/":
        line_end = text.find("\n", start)
        return len(text) if line_end == -1 else line_end

    block_end = text.find("*/", start + 2)
    return len(text) if block_end == -1 else block_end + 2


def lex_code(text: str) -> LexedCode:
    """
    Blank out the comments and string contents of script code, so operators can be matched safely.

    :param text: TypeScript or JavaScript code.
    :return: The code with comments and string contents replaced by spaces, and what was replaced.
    """
    pieces: list[str] = []
    comment_offsets: list[int] = []
    strings: list[StringLiteral] = []
    index = 0
    while index < len(text):
        two_characters = text[index:index + 2]
        if two_characters in ("//", "/*"):
            end = find_comment_end(text, index)
            comment_offsets.append(index)
            pieces.append(blank_out(text[index:end]))
            index = end
            continue

        if text[index] in "'\"`":
            end = find_string_end(text, index)
            literal = text[index:end]
            string_literal = StringLiteral(
                index,
                literal[1:-1],
                text[index] == "`",
            )
            strings.append(string_literal)
            blanked_content = blank_out(literal[1:-1])
            blanked_literal = literal[0] + blanked_content + literal[-1:]
            pieces.append(blanked_literal)
            index = end
            continue

        pieces.append(text[index])
        index += 1
    return LexedCode(
        "".join(pieces),
        comment_offsets,
        strings,
    )


def split_blocks(path: Path, source: str) -> list[SourceBlock]:
    """
    Split a file into the blocks the checks run on.

    :param path: The file being checked.
    :param source: The file's text.
    :return: The template, script, and style blocks of a .vue file, or one script block for a .ts file.
    """
    if path.suffix != ".vue":
        whole_file = SourceBlock(
            "script",
            "",
            source,
            1,
        )
        return [whole_file]

    blocks: list[SourceBlock] = []
    for block_match in BLOCK_PATTERN.finditer(source):
        content_start = block_match.start(3)
        block = SourceBlock(
            block_match.group(1),
            block_match.group(2),
            block_match.group(3),
            line_of(source, content_start),
        )
        blocks.append(block)
    return blocks


def make_violation(
    path: Path,
    block: SourceBlock,
    offset: int,
    rule_id: str,
    message: str,
) -> Violation:
    """
    Build a violation at an offset inside a block.
    """
    line_in_block = line_of(block.text, offset)
    return Violation(
        path,
        block.start_line + line_in_block - 1,
        rule_id,
        message,
    )


def check_operators(
    path: Path,
    block: SourceBlock,
    code: str,
    base_offset: int,
) -> list[Violation]:
    """
    Check code for the operators the conventions ban (??, ?., !!, || or && picking a value, void).

    :param path: The file being checked.
    :param block: The block the code belongs to.
    :param code: Code with strings and comments already blanked out.
    :param base_offset: Where the code starts inside the block.
    :return: One violation per banned operator.
    """
    violations: list[Violation] = []
    for pattern, rule_id, message in OPERATOR_RULES:
        violations += [
            make_violation(
                path,
                block,
                base_offset + operator_match.start(),
                rule_id,
                message,
            )
            for operator_match in pattern.finditer(code)
        ]
    return violations


def read_code_before(code: str, offset: int) -> str:
    """
    Return the code that comes before an offset, up to the lookback limit.
    """
    lookback_start = max(0, offset - DECLARATION_LOOKBACK_CHARACTERS)
    return code[lookback_start:offset]


def is_constant_value(code: str, string_start: int) -> bool:
    """
    Check whether a string is the whole value of an UPPER_CASE constant (`const NAME = '...'`).

    :param code: The lexed code.
    :param string_start: The offset of the string's opening quote.
    :return: Whether the string directly follows `const NAME =`.
    """
    prefix = read_code_before(code, string_start)
    return CONSTANT_VALUE_PREFIX_PATTERN.search(prefix) is not None


def is_inside_constant(code: str, string_start: int) -> bool:
    """
    Check whether a string belongs to the declaration of an UPPER_CASE constant.

    :param code: The lexed code.
    :param string_start: The offset of the string's opening quote.
    :return: Whether the closest declaration before the string declares an UPPER_CASE name.
    """
    prefix = read_code_before(code, string_start)
    declarations = LAST_DECLARATION_PATTERN.findall(prefix)
    if len(declarations) == 0:
        return False

    return UPPER_NAME_PATTERN.match(declarations[-1]) is not None


def is_short_text(text: str) -> bool:
    """
    Check whether a string has 3 words or fewer.

    :param text: The string's value.
    :return: Whether it has at most 3 words.
    """
    return len(text.split()) <= SHORT_STRING_MAX_WORDS


def check_strings(
    path: Path,
    block: SourceBlock,
    lexed: LexedCode,
) -> list[Violation]:
    """
    Check that long strings are constants and short strings stay inline.

    :param path: The file being checked.
    :param block: The script block.
    :param lexed: The block's lexed code.
    :return: One violation per long inline string and per constant that holds a short string.
    """
    violations: list[Violation] = []
    for string_literal in lexed.strings:
        if string_literal.is_template:
            continue

        start = string_literal.start
        value = string_literal.value
        is_constant = is_constant_value(lexed.code, start)
        is_in_constant = is_inside_constant(lexed.code, start)
        is_long_text = len(value.split()) > SHORT_STRING_MAX_WORDS
        if is_short_text(value) and is_constant:
            message = SHORT_STRING_CONSTANT_MESSAGE
        elif is_long_text and not is_in_constant:
            message = LONG_INLINE_STRING_MESSAGE
        else:
            continue

        violations.append(
            make_violation(
                path,
                block,
                start,
                "VU-22",
                message,
            ),
        )
    return violations


def is_color_string(text: str) -> bool:
    """
    Check whether a string is a color value or holds a color class.

    :param text: The string's value.
    :return: Whether it's a hex, rgb, or hsl color, or contains a palette color class such as `text-red-500`.
    """
    if COLOR_STRING_PATTERN.match(text) is not None:
        return True

    return COLOR_CLASS_PATTERN.search(text) is not None


def check_script_colors(
    path: Path,
    block: SourceBlock,
    lexed: LexedCode,
) -> list[Violation]:
    """
    Check script strings for hard-coded colors and color classes.

    :param path: The file being checked.
    :param block: The script block.
    :param lexed: The block's lexed code.
    :return: One violation per string that is a color or holds a color class.
    """
    return [
        make_violation(
            path,
            block,
            string_literal.start,
            "VU-16",
            COLOR_MESSAGE,
        )
        for string_literal in lexed.strings
        if is_color_string(string_literal.value)
    ]


def find_macro_problem(
    macro: str,
    name: str,
    type_argument: str | None,
    static_code: str,
) -> str | None:
    """
    Find what is wrong with one defineProps or defineEmits call.

    :param macro: `defineProps` or `defineEmits`.
    :param name: The interface name the macro must use (`Props` or `Emits`).
    :param type_argument: The start of the macro's type argument, or None when it has none.
    :param static_code: The lexed code of the <script lang="ts"> block.
    :return: The message template for the problem, or None when the call is right.
    """
    if type_argument is None:
        return RUNTIME_MACRO_MESSAGE

    if type_argument == "{":
        return INLINE_MACRO_TYPE_MESSAGE

    if type_argument != name:
        return WRONG_MACRO_TYPE_MESSAGE

    interface_pattern = rf"\b(?:interface|type)\s+{name}\b"
    if re.search(interface_pattern, static_code) is None:
        return MISSING_INTERFACE_MESSAGE

    return None


def check_macros(
    path: Path,
    setup_block: SourceBlock,
    setup_code: str,
    static_code: str,
) -> list[Violation]:
    """
    Check that defineProps and defineEmits use interfaces named Props and Emits from <script lang="ts">.

    :param path: The file being checked.
    :param setup_block: The <script setup> block.
    :param setup_code: The setup block's lexed code.
    :param static_code: The lexed code of the <script lang="ts"> block (empty when there is none).
    :return: One violation per macro or interface that breaks the rule.
    """
    violations: list[Violation] = []
    for macro, name in MACRO_INTERFACE_NAMES:
        macro_pattern = rf"\b{macro}\s*(<\s*(\{{|[A-Za-z_$][\w$]*))?"
        for macro_match in re.finditer(macro_pattern, setup_code):
            message = find_macro_problem(
                macro,
                name,
                macro_match.group(2),
                static_code,
            )
            if message is None:
                continue

            violations.append(
                make_violation(
                    path,
                    setup_block,
                    macro_match.start(),
                    "VU-27",
                    message.format(
                        macro=macro,
                        name=name,
                    ),
                ),
            )
        interface_pattern = re.compile(
            rf"^\s*(?:interface|type)\s+{name}\b",
            re.MULTILINE,
        )
        interface_matches = interface_pattern.finditer(setup_code)
        violations += [
            make_violation(
                path,
                setup_block,
                interface_match.start(),
                "VU-05",
                INTERFACE_IN_SETUP_MESSAGE.format(name=name),
            )
            for interface_match in interface_matches
        ]
    return violations


def check_script_structure(
    path: Path,
    blocks: list[SourceBlock],
    lexed_blocks: list[LexedCode],
) -> list[Violation]:
    """
    Check the script blocks of a .vue file: no exports, constants outside <script setup>, and the macros.

    :param path: The .vue file being checked.
    :param blocks: The file's blocks.
    :param lexed_blocks: The lexed code of each block, in the same order.
    :return: One violation per export, per constant in <script setup>, and per macro problem.
    """
    violations: list[Violation] = []
    static_code = ""
    setup_parts: list[tuple[SourceBlock, str]] = []
    for block, lexed in zip(blocks, lexed_blocks):
        if block.kind != "script":
            continue

        violations += [
            make_violation(
                path,
                block,
                export_match.start(),
                "VU-32",
                EXPORT_MESSAGE,
            )
            for export_match in EXPORT_PATTERN.finditer(lexed.code)
        ]
        if not block.is_setup_script():
            static_code += lexed.code
            continue

        setup_code = lexed.code
        setup_parts.append((block, setup_code))
        constants = SETUP_CONSTANT_PATTERN.finditer(setup_code)
        violations += [
            make_violation(
                path,
                block,
                constant_match.start(),
                "VU-05",
                CONSTANT_IN_SETUP_MESSAGE,
            )
            for constant_match in constants
        ]
    for setup_block, setup_code in setup_parts:
        violations += check_macros(
            path,
            setup_block,
            setup_code,
            static_code,
        )
    return violations


def find_style_attribute_colors(template: str) -> list[int]:
    """
    Find the hard-coded colors inside the style attributes of a template.

    :param template: The template text, with comments blanked out.
    :return: The offset of every color found inside a `style="..."` or `:style="..."` value.
    """
    offsets: list[int] = []
    for style_match in STYLE_ATTRIBUTE_PATTERN.finditer(template):
        style_value = style_match.group(1)
        color_matches = [
            *CSS_COLOR_VALUE_PATTERN.finditer(style_value),
            *CSS_NAMED_COLOR_PATTERN.finditer(style_value),
        ]
        offsets += [
            style_match.start(1) + color_match.start()
            for color_match in color_matches
        ]
    return offsets


def check_template(path: Path, block: SourceBlock) -> list[Violation]:
    """
    Check a <template> block: comments, operators in bindings, and hard-coded colors.

    :param path: The file being checked.
    :param block: The template block.
    :return: Every violation found in the template.
    """
    comment_matches = HTML_COMMENT_PATTERN.finditer(block.text)
    violations = [
        make_violation(
            path,
            block,
            comment_match.start(),
            "VU-40",
            COMMENT_MESSAGE,
        )
        for comment_match in comment_matches
    ]
    template = HTML_COMMENT_PATTERN.sub(blank_match, block.text)
    expression_matches = [
        *TEMPLATE_BINDING_PATTERN.finditer(template),
        *TEMPLATE_INTERPOLATION_PATTERN.finditer(template),
    ]
    for expression_match in expression_matches:
        lexed = lex_code(expression_match.group(1))
        violations += check_operators(
            path,
            block,
            lexed.code,
            expression_match.start(1),
        )
    color_offsets = [
        color_match.start()
        for color_match in [
            *COLOR_CLASS_PATTERN.finditer(template),
            *COLOR_ATTRIBUTE_PATTERN.finditer(template),
        ]
    ]
    color_offsets += find_style_attribute_colors(template)
    violations += [
        make_violation(
            path,
            block,
            color_offset,
            "VU-16",
            COLOR_MESSAGE,
        )
        for color_offset in color_offsets
    ]
    return violations


def check_style(
    path: Path,
    block: SourceBlock,
    is_theme_file: bool,
) -> list[Violation]:
    """
    Check a <style> block for comments and hard-coded colors.

    :param path: The file being checked.
    :param block: The style block.
    :param is_theme_file: Whether the file defines the theme, so it may hold colors.
    :return: One violation per comment and per hard-coded color.
    """
    violations = [
        make_violation(
            path,
            block,
            comment_match.start(),
            "VU-40",
            COMMENT_MESSAGE,
        )
        for comment_match in CSS_COMMENT_PATTERN.finditer(block.text)
    ]
    if is_theme_file:
        return violations

    style = CSS_COMMENT_PATTERN.sub(blank_match, block.text)
    color_matches = [
        *CSS_COLOR_VALUE_PATTERN.finditer(style),
        *CSS_NAMED_COLOR_PATTERN.finditer(style),
    ]
    violations += [
        make_violation(
            path,
            block,
            color_match.start(),
            "VU-16",
            COLOR_MESSAGE,
        )
        for color_match in color_matches
    ]
    return violations


def check_script(
    path: Path,
    block: SourceBlock,
    lexed: LexedCode,
) -> list[Violation]:
    """
    Check one script block: comments, banned operators, colors, and strings.

    :param path: The file being checked.
    :param block: The script block (or the whole .ts file).
    :param lexed: The block's lexed code.
    :return: Every violation found in the script.
    """
    violations = [
        make_violation(
            path,
            block,
            comment_offset,
            "VU-40",
            COMMENT_MESSAGE,
        )
        for comment_offset in lexed.comment_offsets
    ]
    violations += check_operators(
        path,
        block,
        lexed.code,
        0,
    )
    if path.name not in THEME_FILE_NAMES:
        violations += check_script_colors(
            path,
            block,
            lexed,
        )

    if TEST_FILE_PATTERN.search(path.name) is None:
        violations += check_strings(
            path,
            block,
            lexed,
        )

    return violations


def check_vue_file(path: Path) -> list[Violation]:
    """
    Run every check on one .vue or .ts file.

    :param path: The file to check.
    :return: All violations found, sorted by line.
    """
    source = path.read_text(encoding="utf-8-sig")
    is_theme_file = path.name in THEME_FILE_NAMES
    blocks = split_blocks(path, source)
    lexed_blocks = [
        lex_code(block.text)
        for block in blocks
    ]
    violations: list[Violation] = []
    for block, lexed in zip(blocks, lexed_blocks):
        if block.kind == "template":
            violations += check_template(path, block)
        elif block.kind == "style":
            violations += check_style(
                path,
                block,
                is_theme_file,
            )
        else:
            violations += check_script(
                path,
                block,
                lexed,
            )

    if path.suffix == ".vue":
        violations += check_script_structure(
            path,
            blocks,
            lexed_blocks,
        )

    return sorted(violations, key=lambda violation: violation.line)


def check_changed_vue_file(path: Path, base: str) -> list[Violation]:
    """
    Run every check on one file and keep what applies to the lines the branch wrote.

    :param path: The file to check.
    :param base: The git ref the branch is compared to, or `auto`.
    :return: Every violation of a new file. For an existing file the branch changed, the structure rules
        (Props/Emits, constants placement, exports) on the whole file, and the other rules on changed lines.
    """
    changed_lines = get_changed_lines(path, base)
    is_untouched = len(changed_lines.line_numbers) == 0
    if not changed_lines.is_new_file and is_untouched:
        return []

    return [
        violation
        for violation in check_vue_file(path)
        if violation.rule_id in STRUCTURE_RULE_IDS
        or changed_lines.includes(violation.line)
    ]


def collect_frontend_files(raw_paths: list[str]) -> list[Path]:
    """
    Collect the .vue and .ts files in the given files and directories.
    """
    frontend_files: list[Path] = []
    for raw_path in raw_paths:
        path = Path(raw_path)
        if path.is_file() and path.suffix in FRONTEND_SUFFIXES:
            frontend_files.append(path)
            continue

        if not path.is_dir():
            continue

        frontend_files += [
            candidate
            for candidate in sorted(path.rglob("*"))
            if candidate.suffix in FRONTEND_SUFFIXES
            if SKIPPED_DIRECTORY_NAMES.isdisjoint(candidate.parts)
        ]
    return frontend_files


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
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument(
        "paths",
        nargs="+",
        help=PATHS_HELP,
    )
    parser.add_argument(
        "--since",
        default=None,
        help=SINCE_HELP,
    )
    parsed_arguments = parser.parse_args()
    violations: list[Violation] = []
    frontend_files = collect_frontend_files(parsed_arguments.paths)
    for frontend_file in frontend_files:
        if parsed_arguments.since is None:
            violations += check_vue_file(frontend_file)
            continue

        violations += check_changed_vue_file(
            frontend_file,
            parsed_arguments.since,
        )
    if len(violations) == 0:
        return 0

    for violation in violations:
        write_utf8(violation.format_for_output() + "\n")
    write_utf8(f"{len(violations)} convention violation(s).\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
