# Copyright (c) Microsoft Corporation.
# SPDX-License-Identifier: MIT
"""Command-level tests for GitLab issue-management commands."""

from __future__ import annotations

from collections.abc import Callable

import gitlab
import pytest
from conftest import RequestRecorder, StdinFactory
from test_constants import (
    FIELDS_ISSUE,
    FIELDS_MILESTONE,
    TEST_API_URL,
    TEST_PROJECT_ENCODED,
    USAGE_ISSUE_ADD_NOTE,
    USAGE_ISSUE_CREATE,
    USAGE_ISSUE_GET,
    USAGE_ISSUE_UPDATE,
)

CommandFn = Callable[[list[str]], None]

ISSUE_SEARCH_DEFAULT_URL = (
    f"{TEST_API_URL}/projects/{TEST_PROJECT_ENCODED}/issues?state=opened&"
    "per_page=20&order_by=created_at&sort=desc"
)
ISSUE_SEARCH_CUSTOM_URL = (
    f"{TEST_API_URL}/projects/{TEST_PROJECT_ENCODED}/issues?state=closed&"
    "per_page=5&order_by=created_at&sort=desc"
)
ISSUE_GET_URL = f"{TEST_API_URL}/projects/{TEST_PROJECT_ENCODED}/issues/42"
ISSUE_CREATE_URL = f"{TEST_API_URL}/projects/{TEST_PROJECT_ENCODED}/issues"
ISSUE_UPDATE_URL = f"{TEST_API_URL}/projects/{TEST_PROJECT_ENCODED}/issues/9"
ISSUE_NOTES_URL = f"{TEST_API_URL}/projects/{TEST_PROJECT_ENCODED}/issues/5/notes"
MILESTONES_DEFAULT_URL = (
    f"{TEST_API_URL}/projects/{TEST_PROJECT_ENCODED}/milestones?per_page=20"
)
MILESTONES_CUSTOM_URL = (
    f"{TEST_API_URL}/projects/{TEST_PROJECT_ENCODED}/milestones?per_page=100"
)

ISSUE_LIST_RESPONSE = [{"iid": 1, "title": "Bug"}]
ISSUE_GET_RESPONSE = {"iid": 42, "title": "Bug"}
MILESTONE_LIST_RESPONSE = [{"id": 7, "title": "v1.0"}]


def _configure(
    monkeypatch: pytest.MonkeyPatch,
    request_recorder: RequestRecorder,
    response: object | None = None,
) -> RequestRecorder:
    gitlab.api_url = TEST_API_URL
    request_recorder.response = response
    monkeypatch.setattr(gitlab, "project", lambda: TEST_PROJECT_ENCODED)
    monkeypatch.setattr(gitlab, "request", request_recorder)
    return request_recorder


def _capture_print_fields(monkeypatch: pytest.MonkeyPatch) -> list[object]:
    printed: list[object] = []
    monkeypatch.setattr(gitlab, "print_fields", printed.append)
    return printed


def _assert_usage_error(
    command: CommandFn,
    args: list[str],
    expected_message: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        command(args)

    assert exc_info.value.code == gitlab.EXIT_USAGE
    assert expected_message in capsys.readouterr().err


@pytest.mark.parametrize(
    ("command", "args", "expected_message"),
    [
        (gitlab.cmd_issue_get, [], USAGE_ISSUE_GET),
        (gitlab.cmd_issue_update, [], "usage: gitlab issue-update <issue-iid> <json>"),
        (
            gitlab.cmd_issue_add_note,
            [],
            "usage: gitlab issue-add-note <issue-iid> <body>",
        ),
    ],
)
def test_issue_commands_require_minimum_arguments(
    command: CommandFn,
    args: list[str],
    expected_message: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _assert_usage_error(command, args, expected_message, capsys)


def test_issue_search_uses_default_state_and_page_size(
    monkeypatch: pytest.MonkeyPatch,
    request_recorder: RequestRecorder,
) -> None:
    recorder = _configure(monkeypatch, request_recorder, response=[])

    gitlab.cmd_issue_search([])

    assert recorder.calls[0].method == "GET"
    assert recorder.calls[0].url == ISSUE_SEARCH_DEFAULT_URL
    assert recorder.calls[0].quiet is False


def test_issue_search_honors_state_and_max(
    monkeypatch: pytest.MonkeyPatch,
    request_recorder: RequestRecorder,
) -> None:
    recorder = _configure(monkeypatch, request_recorder, response=[])

    gitlab.cmd_issue_search(["closed", "5"])

    assert recorder.calls[0].url == ISSUE_SEARCH_CUSTOM_URL


def test_issue_search_rejects_non_numeric_max(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _assert_usage_error(
        gitlab.cmd_issue_search,
        ["opened", "five"],
        "max_results must be a positive integer",
        capsys,
    )


def test_issue_get_rejects_non_numeric_iid(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _assert_usage_error(
        gitlab.cmd_issue_get,
        ["abc"],
        "expected numeric ID",
        capsys,
    )


@pytest.mark.parametrize(
    ("command", "args", "expected_url"),
    [
        (gitlab.cmd_issue_get, ["42"], ISSUE_GET_URL),
    ],
)
def test_issue_get_builds_expected_url(
    monkeypatch: pytest.MonkeyPatch,
    request_recorder: RequestRecorder,
    command: CommandFn,
    args: list[str],
    expected_url: str,
) -> None:
    recorder = _configure(monkeypatch, request_recorder, response={})

    command(args)

    assert recorder.calls[0].method == "GET"
    assert recorder.calls[0].url == expected_url
    assert recorder.calls[0].quiet is False


@pytest.mark.parametrize(
    ("command", "args", "selected_fields", "response", "expected_printed"),
    [
        (
            gitlab.cmd_issue_search,
            ["opened", "5"],
            FIELDS_ISSUE,
            ISSUE_LIST_RESPONSE,
            ISSUE_LIST_RESPONSE,
        ),
        (
            gitlab.cmd_issue_get,
            ["42"],
            FIELDS_ISSUE,
            ISSUE_GET_RESPONSE,
            ISSUE_GET_RESPONSE,
        ),
        (
            gitlab.cmd_issue_list_milestones,
            [],
            FIELDS_MILESTONE,
            MILESTONE_LIST_RESPONSE,
            MILESTONE_LIST_RESPONSE,
        ),
    ],
)
def test_issue_read_commands_print_selected_fields(
    monkeypatch: pytest.MonkeyPatch,
    request_recorder: RequestRecorder,
    command: CommandFn,
    args: list[str],
    selected_fields: list[str],
    response: object,
    expected_printed: object,
) -> None:
    gitlab.selected_fields = selected_fields
    recorder = _configure(monkeypatch, request_recorder, response=response)
    printed = _capture_print_fields(monkeypatch)

    command(args)

    assert recorder.calls[0].quiet is True
    assert printed == [expected_printed]


def test_issue_list_milestones_uses_default_page_size(
    monkeypatch: pytest.MonkeyPatch,
    request_recorder: RequestRecorder,
) -> None:
    recorder = _configure(monkeypatch, request_recorder, response=[])

    gitlab.cmd_issue_list_milestones([])

    assert recorder.calls[0].method == "GET"
    assert recorder.calls[0].url == MILESTONES_DEFAULT_URL


def test_issue_list_milestones_accepts_custom_max(
    monkeypatch: pytest.MonkeyPatch,
    request_recorder: RequestRecorder,
) -> None:
    recorder = _configure(monkeypatch, request_recorder, response=[])

    gitlab.cmd_issue_list_milestones(["100"])

    assert recorder.calls[0].url == MILESTONES_CUSTOM_URL


@pytest.mark.parametrize(
    ("command", "args", "expected_url", "expected_data"),
    [
        (
            gitlab.cmd_issue_create,
            ['{"title": "Bug"}'],
            ISSUE_CREATE_URL,
            {"title": "Bug"},
        ),
        (
            gitlab.cmd_issue_update,
            ["9", '{"state_event": "close"}'],
            ISSUE_UPDATE_URL,
            {"state_event": "close"},
        ),
        (
            gitlab.cmd_issue_add_note,
            ["5", "Investigating"],
            ISSUE_NOTES_URL,
            {"body": "Investigating"},
        ),
    ],
)
def test_issue_write_commands_forward_inline_payloads(
    monkeypatch: pytest.MonkeyPatch,
    request_recorder: RequestRecorder,
    command: CommandFn,
    args: list[str],
    expected_url: str,
    expected_data: object,
) -> None:
    recorder = _configure(monkeypatch, request_recorder)

    command(args)

    assert recorder.calls[0].url == expected_url
    assert recorder.calls[0].data == expected_data


@pytest.mark.parametrize(
    ("command", "args", "stdin_text", "expected_url", "expected_data"),
    [
        (
            gitlab.cmd_issue_create,
            [],
            '{"title": "stdin issue"}',
            ISSUE_CREATE_URL,
            {"title": "stdin issue"},
        ),
        (
            gitlab.cmd_issue_update,
            ["9"],
            '{"description": "from stdin"}',
            ISSUE_UPDATE_URL,
            {"description": "from stdin"},
        ),
        (
            gitlab.cmd_issue_add_note,
            ["5"],
            "Reproduced on Safari",
            ISSUE_NOTES_URL,
            {"body": "Reproduced on Safari"},
        ),
    ],
)
def test_issue_write_commands_read_payloads_from_stdin(
    monkeypatch: pytest.MonkeyPatch,
    request_recorder: RequestRecorder,
    stdin_factory: StdinFactory,
    command: CommandFn,
    args: list[str],
    stdin_text: str,
    expected_url: str,
    expected_data: object,
) -> None:
    recorder = _configure(monkeypatch, request_recorder)
    stdin_factory(stdin_text)

    command(args)

    assert recorder.calls[0].url == expected_url
    assert recorder.calls[0].data == expected_data


@pytest.mark.parametrize(
    ("command", "args", "usage_message"),
    [
        (gitlab.cmd_issue_create, [], USAGE_ISSUE_CREATE),
        (gitlab.cmd_issue_update, ["9"], USAGE_ISSUE_UPDATE),
        (gitlab.cmd_issue_add_note, ["5"], USAGE_ISSUE_ADD_NOTE),
    ],
)
def test_issue_write_commands_require_stdin_or_inline_content(
    stdin_factory: StdinFactory,
    command: CommandFn,
    args: list[str],
    usage_message: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    stdin_factory("")

    _assert_usage_error(command, args, usage_message, capsys)


def test_issue_create_rejects_invalid_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _assert_usage_error(
        gitlab.cmd_issue_create,
        ["not-json"],
        "invalid JSON payload",
        capsys,
    )


def test_commands_table_registers_issue_commands() -> None:
    expected = {
        "issue-search": gitlab.cmd_issue_search,
        "issue-get": gitlab.cmd_issue_get,
        "issue-create": gitlab.cmd_issue_create,
        "issue-update": gitlab.cmd_issue_update,
        "issue-list-milestones": gitlab.cmd_issue_list_milestones,
        "issue-add-note": gitlab.cmd_issue_add_note,
    }
    for name, handler in expected.items():
        assert gitlab.COMMANDS[name] is handler
