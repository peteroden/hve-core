---
description: 'Execute a Jira backlog plan by creating, updating, transitioning, and commenting on issues from a handoff file'
agent: Jira Backlog Manager
argument-hint: "handoff=... [autonomy={full|partial|manual}] [dryRun={true|false}]"
---

# Execute Jira Backlog Plan

Process a handoff plan file to execute planned Jira operations. The workflow initializes or resumes execution state, processes operations in fixed order, and produces a completion report with issue keys.

Follow all instructions from #file:../../instructions/jira/jira-backlog-update.instructions.md while executing this workflow.
Follow all instructions from #file:../../instructions/jira/jira-backlog-planning.instructions.md for shared conventions.

## Inputs

* `${input:handoff}`: (Required) Path to the handoff plan file (`handoff.md` or `triage-plan.md`).
* `${input:autonomy:partial}`: (Optional, defaults to partial) Autonomy tier controlling confirmation gates. Values: `full`, `partial`, `manual`.
* `${input:dryRun:false}`: (Optional, defaults to false) When true, simulate all operations without modifying Jira state.

## Required Steps

The workflow proceeds through three steps: initialize or resume execution state, process operations in fixed order, then finalize and present a completion report.

### Step 1: Initialize or Resume

1. Read the handoff plan from `${input:handoff}`. When the file is not found, ask the user for the correct path before continuing.
2. Resolve project scope and issue keys from the handoff file header and entries.
3. Check whether `handoff-logs.md` already exists next to `${input:handoff}`:
   * When it exists, rebuild the `{{TEMP-N}}` mapping from completed Create entries and resume from the first unchecked operation.
   * When it does not exist, create `handoff-logs.md` using the template from the planning specification and populate it from the handoff file.
4. Validate the handoff per the update instructions. Abort on critical failures such as missing project scope for create actions; warn and continue on non-critical failures such as an unresolved optional field.
5. Present an execution summary to the user for confirmation before proceeding.

### Step 2: Process Operations

Execute operations in this fixed order: Create, Update, Transition, Comment.

1. Process each operation category in sequence, following the supported operations table and checkpoint protocol in the update instructions.
2. After each Create, resolve the corresponding `{{TEMP-N}}` placeholder to the actual issue key and record the mapping in `handoff-logs.md`.
3. Apply confirmation gates per the Three-Tier Autonomy Model based on `${input:autonomy}`.
4. When `${input:dryRun}` is true, simulate operations per the Dry Run Mode section of the update instructions without executing state-modifying commands.
5. Update checkboxes in the handoff file and append entries to `handoff-logs.md` after each operation.

### Step 3: Finalize and Report

1. Re-read `handoff-logs.md` and compare against the original handoff plan.
2. Process any missed operations that were blocked by dependency failures and have since been unblocked. Limit this retry pass to one additional iteration.
3. Cross-check that all `{{TEMP-N}}` placeholders resolved to actual issue keys.
4. Generate a completion summary with counts for issues created, updated, transitioned, commented, failed, and skipped.
5. When failures occurred, list each failed operation with its error message and suggest corrective actions.

## Success Criteria

* All planned operations from the handoff file are executed or logged with a final status in `handoff-logs.md`.
* All `{{TEMP-N}}` placeholders resolve to actual issue keys or are logged as failed.
* `handoff-logs.md` next to `${input:handoff}` contains an entry for every operation.
* A completion report with Jira issue keys is presented to the user.

## Error Handling

* Handoff file not found: ask the user for the correct path rather than failing silently.
* Missing project key for create actions: abort processing and notify the user.
* Transition not found: log the failure, capture the available transition names, and continue with remaining operations.
* Invalid field update: log the warning and continue with remaining operations.
* Transient network or auth error: stop only when the Jira skill reports a blocking authentication failure; otherwise log and continue.

---

Proceed with executing the backlog plan from `${input:handoff}` following the Required Steps.