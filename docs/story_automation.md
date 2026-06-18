# Story Automation — Implementation Spec

## Goal

Read an Excel sheet describing epics, features, and stories and bulk-create the
matching work items in the `AzureBoardTest` project on Azure DevOps. One
spreadsheet → many work items, with one command.

## Spreadsheet schema

Row 1 must contain these headers exactly (any column order is fine; extras are
ignored):

| Column | Type | Required | Maps to |
|---|---|---|---|
| EPIC                | text   | yes | Epic work item Title |
| FEATURE             | text   | no  | Story tag (`feature:<value>`) |
| STORY               | text   | no  | Local id for your own dedupe; not sent to Azure |
| STORY TITLE         | text   | yes | Issue (Story) Title |
| DESCRIPTION         | text   | no  | Issue Description (HTML allowed) |
| ACCEPTANCE CRITERIA | text   | no  | Appended to Description as `<ol>` |
| STORYPOINTS         | number | no  | `Microsoft.VSTS.Scheduling.Effort` |
| PRIORITY            | int    | no  | `Microsoft.VSTS.Common.Priority` (1–4) |

Multiple rows can share the same EPIC value — the script will create that Epic
**once** and parent all matching Stories under it.

## Hierarchy mapping (why this is necessary)

`AzureBoardTest` uses the **Basic process template**, which only has these work
item types: Epic, Issue, Task. There is no Feature WIT.

| Spreadsheet level | Azure work item | Notes |
|---|---|---|
| EPIC    | `Epic`  | Created once per unique value, cached for the run |
| FEATURE | *(tag)* | Stored on the Story as `feature:<name>` tag — searchable, filterable |
| STORY   | `Issue` | Parented to its Epic via `Hierarchy-Reverse` link |

There is no `Microsoft.VSTS.Common.AcceptanceCriteria` field on Basic either,
so AC is appended to the description as a numbered HTML list.

## Architecture

```
stories.xlsx ──> read_xlsx() ──> list[dict]
                                       │
                       ┌───────────────┴──────────────┐
                       ▼                              ▼
              ensure_epic() (cached)           create_story()
                       │                              │
                       └──────► Azure DevOps REST ◄───┘
```

Single Python file, three functions, no framework. The "agent" layer is the
Claude Code skill at `.claude/skills/story-automation/SKILL.md` that drives
this script.

## Files

| File | Purpose |
|---|---|
| `story_automation.py` | Reader + REST client + CLI entry point |
| `.claude/skills/story-automation/SKILL.md` | Slash command behaviour for Claude Code |
| `docs/story_automation.md` | This document |
| `.env` | `AZURE_DEVOPS_*` variables (already set up) |

## Environment

These must be present in `.env` (already configured from the earlier task):

```
AZURE_DEVOPS_PAT
AZURE_DEVOPS_ORG
AZURE_DEVOPS_PROJECT
AZURE_DEVOPS_AREA_PATH
AZURE_DEVOPS_ITERATION_PATH
```

## Dependencies

Add to `requirements.txt`:

```
openpyxl>=3.1.0
```

Then `pip install -r requirements.txt`.

## Usage

### From the terminal

```bash
# Validate the sheet without hitting Azure
python story_automation.py stories.xlsx --dry-run

# Real run, stop on first failure
python story_automation.py stories.xlsx

# Real run, keep going and report failures at the end
python story_automation.py stories.xlsx --continue-on-error
```

### From Claude Code

In the Claude Code prompt:

```
/story-automation stories.xlsx
```

Claude will: validate the file, run `--dry-run`, show you the summary, ask for
confirmation, then run for real and report the created work item IDs.

## Error handling

Every REST call raises immediately if the status isn't `2xx`, and the error
body from Azure DevOps is printed. The most common failures and what they
mean:

| Symptom | Likely cause |
|---|---|
| `401 Unauthorized` | PAT is wrong, expired, or missing Work Items scope |
| `404 ... Work item type X does not exist` | Wrong process template (this script is built for Basic) |
| `400 ... is not in the list of supported values` | Area/Iteration path doesn't exist in the project |
| `Missing required columns: [...]` | Spreadsheet row 1 doesn't have the expected headers |

## Exit codes

- `0` — success (or `--dry-run` summary printed cleanly)
- `1` — one or more failures (with `--continue-on-error`) or a fatal error

## Out of scope (v1)

- Updating existing work items (only create)
- Cross-file dedupe (the script doesn't check what's already on the board)
- FEATURE as a real work item (not possible on Basic)
- LLM enrichment of titles, descriptions, or AC

## Test plan

1. Build a tiny `test_stories.xlsx` with 1 Epic + 2 Stories.
2. Run `--dry-run` — confirm correct counts.
3. Run for real — verify on board that the Epic was created once and both
   Stories are children of it with the right tag.
4. Run again with a row missing `STORY TITLE` — expect a clear error before any
   Azure call.
