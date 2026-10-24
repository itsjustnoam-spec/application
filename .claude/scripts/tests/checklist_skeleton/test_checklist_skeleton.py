from checklist_skeleton import ChecklistItem, build_answer, find_unanswered_items, read_checklist


def test_read_checklist_reads_every_item_in_order():
    items = read_checklist("sql-conventions")

    assert [
        item.rule_id
        for item in items
    ] == ["SQL-04", "SQL-05", "SQL-01", "SQL-02", "SQL-03"]


def test_build_answer_checker_violation_is_a_failure():
    item = ChecklistItem("PY-52", "No comments (auto)")

    answer = build_answer(item, {"PY-52": ["`app/site.py:4`"]})

    assert answer.startswith("  - ❌ checker: `app/site.py:4`")


def test_build_answer_clean_automatic_item_is_a_pass():
    item = ChecklistItem("PY-52", "No comments (auto)")

    answer = build_answer(item, {})

    assert answer.startswith("  - ✅ checker")


def test_build_answer_manual_item_is_left_to_the_reviewer():
    item = ChecklistItem("PY-22", "Names say exactly what they handle")

    answer = build_answer(item, {})

    assert answer.startswith("  - TODO")


def test_find_unanswered_items_reports_missing_and_todo_items():
    review_text = (
        "- SQL-01 No session.rollback()\n"
        "  - ✅ `app/site.py:10-30`: rollback goes through the transaction\n"
        "- SQL-02 The unit of work owns the transaction\n"
        "  - TODO: ...\n"
    )

    unanswered_ids = find_unanswered_items(["sql-conventions"], review_text)

    assert unanswered_ids == ["SQL-04", "SQL-05", "SQL-02", "SQL-03"]


def test_find_unanswered_items_bare_marks_are_not_answers():
    review_text = (
        "- SQL-04 Indexes in __table_args__\n"
        "  - ✅\n"
        "- SQL-05 Table model layout\n"
        "  - N/A\n"
        "- SQL-01 No session.rollback()\n"
        "  - ❌ (F-C1-2)\n"
        "- SQL-02 The unit of work owns the transaction\n"
        "  - ✅ checker: no violations on the lines this branch wrote\n"
        "- SQL-03 Nested transactions for expected failures\n"
        "  - N/A: no expected failures in the changed managers\n"
    )

    unanswered_ids = find_unanswered_items(["sql-conventions"], review_text)

    assert unanswered_ids == ["SQL-04", "SQL-05", "SQL-01"]
