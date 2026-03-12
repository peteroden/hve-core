---
description: 'Triage Jira issues with bounded JQL, field recommendations, duplicate detection, and optional execution of confirmed updates'
agent: Jira Backlog Manager
argument-hint: "[project=...] [jql=...] [maxIssues=20] [autonomy={full|partial|manual}]"
---

# Triage Jira Issues

Fetch Jira issues in scope, analyze each for field recommendations and duplicate signals, and produce a triage plan for review before executing confirmed changes.

Follow all instructions from #file:../../instructions/jira/jira-backlog-triage.instructions.md while executing this workflow.
Follow all instructions from #file:../../instructions/jira/jira-backlog-planning.instructions.md for shared conventions.

## Inputs

* `${input:project}`: (Optional) Jira project key used to scope triage when `jql` is not provided.
* `${input:jql}`: (Optional) Explicit bounded JQL query selecting the issues to triage.
* `${input:maxIssues:20}`: (Optional, defaults to 20) Maximum issues to process per batch.
* `${input:autonomy:partial}`: (Optional, defaults to partial) Autonomy tier controlling confirmation gates. Values: `full`, `partial`, `manual`.

## Required Steps

The workflow proceeds through three steps: fetch in-scope issues, analyze each issue for recommendations, then present and execute confirmed changes.

### Step 1: Fetch Triage Candidates

1. Build the triage query from `${input:jql}` when provided.
2. When `${input:jql}` is not provided and `${input:project}` is available, use a bounded default query such as `project = <project> AND statusCategory != Done ORDER BY created DESC`.
3. Execute `.github/skills/jira/jira/scripts/jira.py search '<jql>' ${input:maxIssues} --fields key,fields.summary,fields.status.name,fields.priority.name,fields.labels`.
4. Hydrate each candidate with `.github/skills/jira/jira/scripts/jira.py get <ISSUE-KEY> --fields ...`.
5. Create the planning directory at `.copilot-tracking/jira-issues/triage/{{YYYY-MM-DD}}/` and record fetched issues in `planning-log.md`.

When no issues are returned, inform the user and suggest broadening the JQL or providing a different project scope.

### Step 2: Analyze and Classify

For each fetched issue, perform these analyses and build triage recommendations.

1. Parse the summary for conventional-commit-like prefixes or consistent team prefixes when present. Use that signal to suggest issue type, labels, and relative priority.
2. Review labels, status, assignee, and priority for gaps or conflicts.
3. Search for potential duplicates using narrow JQL built from the issue summary and key terms.
4. Recommend one or more actions:
   * Update fields, such as labels, priority, summary, or assignee
   * Transition status when the issue is clearly in the wrong workflow state
   * Comment when coordination context should be added without changing fields
   * No Change when the issue already matches expectations
5. Record the analysis in `triage-plan.md` using the template from the triage instructions.

### Step 3: Present and Execute

Present the triage plan to the user as a summary table, then apply confirmed recommendations according to `${input:autonomy}`.

1. Under `full`, execute all supported changes immediately.
2. Under `partial`, auto-execute low-risk field updates, but gate transitions and duplicate-handling comments on user approval.
3. Under `manual`, wait for user confirmation before each Jira mutation.
4. Apply confirmed changes using the Jira skill commands defined in the triage instructions.
5. Update `planning-log.md` with execution results for each processed issue.

## Success Criteria

* All fetched issues have triage recommendations with labels, priority, status, assignee, or comment suggestions when applicable.
* The triage plan is reviewed according to the active autonomy tier before gated execution.
* Planning artifacts are created in `.copilot-tracking/jira-issues/triage/{{YYYY-MM-DD}}/`.
* Executed changes use only supported Jira skill commands.

## Error Handling

* No issues found: inform the user and suggest broadening the query.
* Missing project scope and no `jql` provided: ask the user for one of them before proceeding.
* Duplicate detection ambiguous: flag the issue as Uncertain and present the candidates for review.
* Concurrent modification: re-fetch the issue before applying updates when the planning data appears stale.

---

Proceed with triaging Jira issues following the Required Steps.