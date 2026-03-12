---
description: 'Discover Jira issues through user-centric queries, artifact-driven analysis, or JQL-based exploration and produce planning files for review'
agent: Jira Backlog Manager
argument-hint: "[project=...] [documents=...] [jql=...] [searchTerms=...]"
---

# Discover Jira Issues

Classify the discovery path based on user intent and available inputs, execute the appropriate discovery workflow, and produce planning files for review when the workflow is artifact-driven. Three discovery paths are supported: user-centric queries, artifact-driven analysis from documents, and JQL-based exploration.

Follow all instructions from #file:../../instructions/jira/jira-backlog-discovery.instructions.md while executing this workflow.
Follow all instructions from #file:../../instructions/jira/jira-backlog-planning.instructions.md for shared conventions.

## Inputs

* `${input:project}`: (Optional) Jira project key used to scope searches, field discovery, and issue creation plans.
* `${input:documents}`: (Optional) Document paths or attached files to analyze for issue extraction. Triggers artifact-driven discovery when provided.
* `${input:jql}`: (Optional) Explicit JQL query to execute. Triggers JQL-based discovery when provided.
* `${input:searchTerms}`: (Optional) Plain-language search terms to convert into bounded JQL when `jql` is not provided.
* `${input:includeComments:false}`: (Optional, defaults to false) Include issue comments in hydrated discovery results.
* `${input:autonomy:partial}`: (Optional, defaults to partial) Autonomy tier controlling confirmation gates during handoff review. Values: `full`, `partial`, `manual`.

## Required Steps

The workflow proceeds through four steps: classify the discovery path, execute discovery for the selected path, assess planned actions for artifact-driven discovery, then assemble planning files and present them for review.

### Step 1: Classify and Initialize

Resolve the Jira project scope from `${input:project}`, the active workspace context, or the source documents before classifying the discovery path.

1. Classify the discovery path based on inputs and user intent:
   * Path A (User-Centric): User requests assigned issues or backlog visibility without source documents, JQL, or search terms.
   * Path B (Artifact-Driven): Documents or requirements are provided via `${input:documents}` or conversation.
   * Path C (JQL-Based): User provides `${input:jql}` directly, or provides `${input:searchTerms}` that can be converted into bounded JQL.
2. Create the planning folder at `.copilot-tracking/jira-issues/discovery/<scope-name>/` and initialize `planning-log.md`.
3. When Path B is selected and `${input:project}` is available, inspect available issue types and create-field requirements with `.github/skills/jira/jira/scripts/jira.py fields <project>`.

When neither documents nor search inputs are provided and user intent does not indicate assigned-issue retrieval, ask the user to clarify the discovery goal before proceeding.

### Step 2: Execute Discovery

Run the discovery workflow for the classified path. Paths A and C produce a conversational summary and complete the workflow. Path B continues to Steps 3 and 4.

#### Path A: User-Centric Discovery

1. Build a bounded JQL query for the authenticated user. Prefer `project = <project> AND assignee = currentUser() ORDER BY updated DESC` when a project key is known.
2. Execute `.github/skills/jira/jira/scripts/jira.py search '<jql>' --fields key,fields.summary,fields.status.name,fields.priority.name`.
3. Hydrate issues with `.github/skills/jira/jira/scripts/jira.py get <ISSUE-KEY> --fields ...` for entries requiring additional detail. When `${input:includeComments}` is true, call `comments` for each hydrated issue.
4. Present results grouped by status.
5. Log discovered issues in `planning-log.md` and deliver a conversational summary.
6. Skip Steps 3 and 4.

#### Path B: Artifact-Driven Discovery

1. Read each document referenced in `${input:documents}` to completion.
2. Extract discrete requirements, acceptance criteria, and action items using the document parsing guidance from the discovery instructions.
3. Record each extracted requirement as a candidate issue entry in `issue-analysis.md` with a temporary planning ID, suggested summary, suggested issue type, suggested labels, suggested priority, and source reference.
4. Build bounded JQL search queries from the extracted requirements.
5. Execute `.github/skills/jira/jira/scripts/jira.py search '<jql>' --fields key,fields.summary,fields.status.name,fields.priority.name,fields.labels` for each query.
6. Hydrate promising matches with `.github/skills/jira/jira/scripts/jira.py get <ISSUE-KEY> --fields ...`.
7. Log search queries, result counts, and progress in `planning-log.md`.
8. Continue to Step 3.

#### Path C: JQL-Based Discovery

1. Use `${input:jql}` directly when provided. Otherwise, convert `${input:searchTerms}` into a bounded JQL query using project scope, labels, assignee, status, or text search clauses.
2. Execute `.github/skills/jira/jira/scripts/jira.py search '<jql>' --fields key,fields.summary,fields.status.name,fields.priority.name,fields.labels`.
3. Hydrate issues with `.github/skills/jira/jira/scripts/jira.py get <ISSUE-KEY> --fields ...` for entries requiring additional detail. When `${input:includeComments}` is true, call `comments` for each hydrated issue.
4. Present results grouped by status and priority.
5. Log discovered issues in `planning-log.md` and deliver a conversational summary.
6. Skip Steps 3 and 4.

### Step 3: Assess Similarity and Plan Actions

This step applies to Path B only.

1. Assess similarity between each candidate and each hydrated Jira issue using the Similarity Assessment Framework from the planning specification. Classify each pair as Match, Similar, Distinct, or Uncertain.
2. De-duplicate results across JQL searches. Retain the highest similarity category when the same issue appears multiple times.
3. Categorize each candidate into an action:
   * Create: Distinct candidates with no existing coverage
   * Update: Match candidates where fields or description need refinement
   * Transition: Existing issues that require a status move instead of field changes
   * Comment: Existing issues that need context appended without field mutation
   * No Change: Existing issues already covering the requirement
4. Record all planned operations in `issue-analysis.md` and `issues-plan.md` with rationale.
5. Update `planning-log.md` with the current phase status and similarity assessment results.

Pause and request user guidance when human review triggers are met, including ambiguous requirements, multiple Similar results for a single candidate, missing project scope for new issues, or Uncertain assessments.

### Step 4: Assemble Handoff and Present

This step applies to Path B only.

1. Build `handoff.md` per the template in the planning specification. Order entries as Create first, Update second, Transition third, Comment fourth, No Change last.
2. Include checkboxes, summaries, target fields, and artifact references for each entry.
3. Add a Planning Files section with project-relative paths to all generated files.
4. Apply the Three-Tier Autonomy Model from the planning specification to determine confirmation gates based on `${input:autonomy}`.
5. Verify consistency across `issue-analysis.md`, `issues-plan.md`, and `handoff.md` before presenting.
6. Present the handoff for user review, highlighting items that trigger human review.
7. Record the final state in `planning-log.md` with phase completion status.

## Success Criteria

* The discovery path is classified before executing any Jira queries.
* All provided documents are analyzed for actionable items when Path B is selected.
* Existing Jira backlog is searched using bounded JQL derived from extracted requirements or user-provided inputs.
* Similarity assessments classify each candidate-to-existing-issue pair as Match, Similar, Distinct, or Uncertain.
* Path B produces `planning-log.md`, `issue-analysis.md`, `issues-plan.md`, and `handoff.md` in `.copilot-tracking/jira-issues/discovery/<scope-name>/`.
* Paths A and C produce `planning-log.md` and a conversational summary.
* Discovery does not execute Jira mutations.

## Error Handling

* No inputs provided: ask the user to provide documents, JQL, search terms, or clarify the discovery goal before proceeding.
* Search returns no results: broaden the JQL, retry, and log the empty search in `planning-log.md`.
* Ambiguous matches: flag as Uncertain and present the options for user review rather than auto-categorizing.
* Large document: process sections incrementally and record progress in `planning-log.md` after each section.
* Missing project key for creation planning: call `fields` only when the project can be resolved, otherwise pause for user guidance.

---

Proceed with discovering Jira issues following the Required Steps.