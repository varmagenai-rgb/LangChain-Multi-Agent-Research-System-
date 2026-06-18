---
name: story-automation
description: Bulk-create Epic + Story work items on Azure DevOps from an xlsx spreadsheet. Use when the user asks to "upload stories", "import sprint plan", or runs /story-automation with a path to an .xlsx file.
---

# Story Automation

This skill takes an `.xlsx` file describing epics, features, and stories and
creates the matching work items in the configured Azure DevOps project (Basic
process: Epic + Issue).

Two backends exist — pick based on what the user asks for:

| Backend | Use when | Driver |
|---|---|---|
| **v1 (default)** | User wants deterministic, fast, predictable behaviour. **Default for the slash command.** | `story_automation.py` |
| **v2 (agent)** | User explicitly asks for "the Claude agent" or "the agent_framework version". | `python -m story_tools` (interactive REPL using Claude Haiku + agent_framework) |

If the user does not specify, use v1.

## Required spreadsheet headers

`EPIC, FEATURE, STORY, STORY TITLE, DESCRIPTION, ACCEPTANCE CRITERIA, STORYPOINTS, PRIORITY`

## Required environment

Both backends read from `.env`:

```
AZURE_DEVOPS_PAT
AZURE_DEVOPS_ORG
AZURE_DEVOPS_PROJECT
AZURE_DEVOPS_AREA_PATH
AZURE_DEVOPS_ITERATION_PATH
```

v2 additionally reads:

```
AZURE_KEYVAULT_URL
ANTHROPIC_KEY_SECRET_NAME
```

…and requires the user to have run `az login` with the **Key Vault Secrets
User** role on the target vault.

If any are missing, the relevant driver will raise `KeyError` immediately —
do not try to set them yourself, ask the user to update `.env`.

## What to do when invoked (v1 — default)

1. **Get the xlsx path.** If the user passed one in the slash command
   arguments, use it. Otherwise ask: "Which .xlsx file should I upload?".

2. **Confirm the file exists.** Use `Read` on the path. If it doesn't exist,
   stop and tell the user.

3. **Dry-run first.** Always. Run:

   ```bash
   PYTHONIOENCODING=utf-8 python story_automation.py <path> --dry-run
   ```

   This validates headers, counts rows, and lists the unique Epics and
   Features it would create — without touching Azure DevOps.

4. **Show the dry-run output to the user** and explicitly ask for
   confirmation to proceed. Example: "Dry-run looks good — 1 Epic, 3
   Features, 5 Stories. Proceed with the real run?" Do **not** proceed
   without an affirmative answer.

5. **On confirmation, run for real:**

   ```bash
   PYTHONIOENCODING=utf-8 python story_automation.py <path>
   ```

   (Add `--continue-on-error` only if the user asks for it.)

6. **Report.** Print the script output and call out the created work item
   IDs. If anything failed, surface the Azure DevOps error message verbatim —
   don't try to fix or retry.

## What to do when invoked (v2 — the agent)

Use this when the user asks for the agent_framework / Claude version. The v2
backend is an interactive REPL where Claude Haiku itself orchestrates the
tools. You do not pipe commands into it — you launch it and the user takes
over.

1. **Get the xlsx path.** Same as v1.

2. **Confirm the file exists.** Same as v1.

3. **Launch the REPL:**

   ```bash
   PYTHONIOENCODING=utf-8 python -m story_tools
   ```

   The REPL prompt is `you> `. Tell the user to type a sentence like
   `Upload <path>`. The agent will:
   - read the xlsx,
   - show a dry-run summary,
   - ask "Proceed with the real upload?",
   - wait for `yes` or similar from the user,
   - then create the work items and print a markdown results table.

4. **Don't interfere** while the user is in the REPL — that's the agent's
   surface. When the user exits with `quit`, you can summarise what
   happened.

## Things not to do

- Do not modify `story_automation.py`, `story_tools/`, or
  `agent_utils.py` to "fix" Azure DevOps errors. The right response to a
  4xx is to surface it to the user.
- Do not skip the dry-run, even if the user says "just do it" — bulk-creating
  on the board is hard to reverse. The dry-run takes 1 second.
- Do not commit the xlsx file unless the user explicitly asks.
- Do not assume the env vars are set correctly. If a driver raises
  KeyError on any required var, surface it and stop.
- For v2: do not try to drive the REPL via stdin redirection. Launch it
  and let the user interact directly.

## Reference

| What | Where |
|---|---|
| v1 CLI | `story_automation.py` |
| v2 agent driver | `story_tools/__main__.py` |
| v2 tools | `story_tools/_tools.py` |
| v2 system prompt | `story_tools/_agent.py` (`SYSTEM_PROMPT`) |
| Shared actions | `story_tools/_actions.py` |
| Key Vault helper | `story_tools/_secrets.py` |
| v1 design spec | `docs/story_automation.md` |
| v2 plan + checklist | `docs/story_automation_agent_plan.md` |
