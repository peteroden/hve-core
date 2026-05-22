---
name: gitlab
description: 'Manage GitLab merge requests, pipelines, and project issues with a Python CLI - Brought to you by microsoft/hve-core'
license: MIT
compatibility: 'Requires Python 3.11+. GitLab credentials via GITLAB_URL and GITLAB_TOKEN environment variables.'
metadata:
  authors: "microsoft/hve-core"
  spec_version: "1.0"
  last_updated: "2026-03-24"
---

# GitLab Skill

## Overview

Use this skill to inspect and update GitLab merge requests, notes, pipelines,
job logs, and project issues against GitLab.com or self-managed GitLab
instances.

This skill is the repository-local Python workflow for GitLab tasks. It is not
the official GitLab MCP server integration surface.

The current hve-core implementation is Python-only. Run the CLI through
`python scripts/gitlab.py` and prefer `--fields` for read operations to keep
output concise.

## Prerequisites

The skill requires Python 3.11 or later.

Set these environment variables before running any command:

| Variable         | Required | Example              | Purpose                                       |
|------------------|----------|----------------------|-----------------------------------------------|
| `GITLAB_URL`     | Yes      | `https://gitlab.com` | GitLab instance URL                           |
| `GITLAB_TOKEN`   | Yes      | `glpat-...`          | Personal access token sent as `PRIVATE-TOKEN` |
| `GITLAB_PROJECT` | No       | `group/project`      | Project path or numeric project ID            |

If `GITLAB_PROJECT` is not set, the script attempts to detect the project from
`git remote get-url origin`. Set the variable explicitly when you are not in a
git repository or when you want to target a different project.

## Quick Start

Export your environment variables, then run a read command with `--fields`.

```bash
export GITLAB_URL="https://gitlab.com"
export GITLAB_TOKEN="glpat-..."
export GITLAB_PROJECT="group/project"

python scripts/gitlab.py mr-list opened --fields iid,title,author.name
```

Read pipeline jobs for a known pipeline:

```bash
python scripts/gitlab.py pipeline-jobs 12345 --fields id,name,status,stage
```

## Parameters Reference

### Common Option

| Parameter  | Applies To                                                                                                             | Example                    | Description                                                                             |
|------------|------------------------------------------------------------------------------------------------------------------------|----------------------------|-----------------------------------------------------------------------------------------|
| `--fields` | `mr-list`, `mr-get`, `mr-notes`, `pipeline-get`, `pipeline-jobs`, `issue-search`, `issue-get`, `issue-list-milestones` | `--fields iid,title,state` | Extract specific fields with dot notation and print concise tabular or key-value output |

### Commands

| Command                 | Arguments                     | Description                                                                                   |
|-------------------------|-------------------------------|-----------------------------------------------------------------------------------------------|
| `mr-list`               | `[state] [max]`               | List merge requests, defaulting to all states and 20 results                                  |
| `mr-get`                | `<mr-iid>`                    | Get one merge request by project-scoped IID                                                   |
| `mr-create`             | `<json>` or stdin             | Create a merge request from a JSON payload                                                    |
| `mr-update`             | `<mr-iid> <json>` or stdin    | Update merge request fields from a JSON payload                                               |
| `mr-comment`            | `<mr-iid> <body>` or stdin    | Add a comment to a merge request                                                              |
| `mr-notes`              | `<mr-iid> [max]`              | List merge request notes, excluding system notes when using `--fields`                        |
| `pipeline-get`          | `<pipeline-id>`               | Get one pipeline by numeric ID                                                                |
| `pipeline-run`          | `<branch-or-tag>`             | Trigger a pipeline for a branch or tag                                                        |
| `pipeline-jobs`         | `<pipeline-id>`               | List jobs for a pipeline                                                                      |
| `job-log`               | `<job-id>`                    | Print raw log output for a job                                                                |
| `issue-search`          | `[state] [max]`               | List project issues, defaulting to `opened` state and 20 results                              |
| `issue-get`             | `<issue-iid>`                 | Get one issue by project-scoped IID                                                           |
| `issue-create`          | `<json>` or stdin             | Create an issue from a JSON payload                                                           |
| `issue-update`          | `<issue-iid> <json>` or stdin | Update issue fields from a JSON payload                                                       |
| `issue-list-milestones` | `[max]`                       | List project milestones, project-scoped (no `<issue-iid>` required), defaulting to 20 results |
| `issue-add-note`        | `<issue-iid> <body>` or stdin | Add a note (comment) to an issue                                                              |

## Script Reference

List recent open merge requests:

```bash
python scripts/gitlab.py mr-list opened --fields iid,title,author.name,user_notes_count
```

Get one merge request:

```bash
python scripts/gitlab.py mr-get 42 --fields iid,title,state,source_branch,target_branch
```

Create a merge request from inline JSON:

```bash
python scripts/gitlab.py mr-create '{
  "source_branch": "feature/add-auth",
  "target_branch": "main",
  "title": "feat(auth): add OAuth login"
}'
```

Add a merge request comment from standard input:

```bash
echo "CI passed. Ready for review." | python scripts/gitlab.py mr-comment 42
```

Inspect a failed pipeline:

```bash
python scripts/gitlab.py pipeline-get 12345 --fields id,status,web_url
python scripts/gitlab.py pipeline-jobs 12345 --fields id,name,status,stage
python scripts/gitlab.py job-log 67890
```

### Issue Workflows

All issue commands operate against the project resolved from `GITLAB_PROJECT`
or the `origin` git remote. Issue IIDs are project-scoped (the `#123` shown in
the GitLab UI), not global IDs.

List open issues:

```bash
python scripts/gitlab.py issue-search opened 50 --fields iid,title,state,labels
```

Get one issue:

```bash
python scripts/gitlab.py issue-get 42 --fields iid,title,state,labels,milestone.title
```

Create an issue from inline JSON:

```bash
python scripts/gitlab.py issue-create '{
  "title": "Login fails on mobile Safari",
  "description": "Tap on the sign-in button does not submit the form.",
  "labels": "bug,frontend"
}'
```

Update an issue from stdin:

```bash
echo '{"state_event": "close"}' | python scripts/gitlab.py issue-update 42
```

List project milestones:

```bash
python scripts/gitlab.py issue-list-milestones 100 --fields id,iid,title,state,due_date
```

Add a note to an issue:

```bash
echo "Reproduced on Safari 17. Investigating." | python scripts/gitlab.py issue-add-note 42
```

The `issue-search`, `issue-get`, `issue-list-milestones`, `issue-create`, and
`issue-update` commands return the GitLab REST issue or milestone object. The
`issue-add-note` command returns the created note object. Write commands print
the full JSON response by default; pass `--fields` to read commands for tabular
output.

Write commands (`issue-create`, `issue-update`, `issue-add-note`, plus existing MR write commands) intentionally bypass `--fields` and always print the full JSON response.

## Troubleshooting

| Symptom                                          | Cause                                                     | Resolution                                                                                     |
|--------------------------------------------------|-----------------------------------------------------------|------------------------------------------------------------------------------------------------|
| `GITLAB_URL is not set`                          | Required environment variable missing                     | Export `GITLAB_URL` before running the script                                                  |
| `GITLAB_TOKEN is not set`                        | Missing personal access token                             | Create a token with API access and export `GITLAB_TOKEN`                                       |
| `cannot parse git remote URL`                    | Project autodetection failed                              | Set `GITLAB_PROJECT` explicitly                                                                |
| `HTTP 401` or `HTTP 403`                         | Token is invalid or lacks access                          | Verify token scope and project permissions                                                     |
| `HTTP 404`                                       | Wrong project, MR IID, pipeline ID, or job ID             | Verify `GITLAB_PROJECT` and confirm the numeric identifiers                                    |
| `expected numeric ID`                            | Non-numeric value passed to an ID argument                | Use project MR IID values and numeric pipeline or job IDs                                      |
| `python3 is required` or syntax errors on launch | Unsupported interpreter                                   | Run the script with Python 3.11 or later                                                       |
| `HTTP 422`                                       | Invalid field payload on `issue-create` or `issue-update` | Verify JSON keys against the GitLab issues API at <https://docs.gitlab.com/ee/api/issues.html> |

GitLab uses MR IIDs such as `!42` and issue IIDs such as `#42` inside a
project. This skill expects the numeric IID, not the global merge request or
issue ID.

*🤖 Crafted with precision by ✨Copilot following brilliant human instruction, then carefully refined by our team of discerning human reviewers.*
