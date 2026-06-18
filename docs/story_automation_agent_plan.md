# Story Automation v2 — Claude Agent Implementation Plan

## Decisions locked in

| Decision | Chosen | Implication |
|---|---|---|
| LLM | `claude-haiku-4-5` | Cheapest, fastest; tool-use sometimes needs nudging. We'll mitigate with a tight system prompt and a Sonnet fallback path. |
| Approval style | Multi-turn `AgentSession` | Agent shows dry-run, returns, waits for user's "go ahead" in chat. No per-tool gating. |
| API key source | Azure Key Vault | Fetched at startup with `AzureCliCredential`, never stored in `.env`. |
| Layout | `story_tools/` package | Clean separation: `_actions.py`, `_tools.py`, `_agent.py`, `__main__.py`. |

## Goal

Replace the v1 deterministic CLI (`story_automation.py`) with a true agent
implementation that combines:

- **Microsoft Agent Framework** (`agent_framework.Agent` + `@tool` + `AgentSession`)
- **Anthropic Claude Haiku 4.5** as the LLM
- **Azure Key Vault** for the Anthropic API key
- **Azure DevOps REST** as the side-effecting backend
- **Anthropic prompt-engineering standards** in the system prompt

User experience:

> User: *"Upload `test_stories.xlsx`."*
> Agent: *"Loaded 3 rows: 1 Epic, 2 Features, 3 Stories. Proceed?"*
> User: *"Yes."*
> Agent: *"Created Epic #N and Stories #N #N #N."*

## How this differs from v1

| Concern | v1 (current) | v2 (this plan) |
|---|---|---|
| Orchestration | argparse + `if/else` | LLM picks which tool to call |
| LLM | None | Anthropic Claude Haiku 4.5 |
| Tools | Plain Python functions | `@tool`-decorated, schema-introspected by the agent |
| User interaction | CLI flags | Natural-language conversation |
| Safety | `--dry-run` flag | Multi-turn `AgentSession`: dry-run → confirm → apply |
| API key | `.env` | Azure Key Vault via `AzureCliCredential` |
| Reusability | Single CLI | Tools in `story_tools/` package, reusable by other agents |

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  User (chat)                                                     │
│   │                                                              │
│   ▼                                                              │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ agent_framework.Agent + AgentSession                       │  │
│  │  • System prompt (Claude best practices, XML-structured)   │  │
│  │  • Tools: read_stories, dry_run_summary,                   │  │
│  │           create_epic, create_story                        │  │
│  │  • Client: AnthropicClient(model="claude-haiku-4-5")       │  │
│  └────────────────────────────────────────────────────────────┘  │
│           │                       │                              │
│           ▼                       ▼                              │
│   Claude reasoning loop    Tool calls (Python)                   │
│                                   │                              │
│                                   ▼                              │
│              Azure DevOps REST  (Epic + Issue, via PAT)          │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Bootstrap (once, at process start):                        │  │
│  │   AzureCliCredential → SecretClient → ANTHROPIC_API_KEY    │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

## Tech stack

| Layer | Package | Already installed? |
|---|---|---|
| Agent runtime | `agent_framework` | ✅ |
| Claude client | `agent_framework_anthropic` (`AnthropicClient`) | ✅ |
| Key Vault | `azure-keyvault-secrets` | ❓ probably needs `pip install` |
| Azure auth | `azure-identity` | ✅ (already used by FoundryChatClient) |
| xlsx reader | `openpyxl` | ✅ (3.1.5) |
| HTTP | `requests` | ✅ |
| Env loading | `python-dotenv` | ✅ |

Claude model: **`claude-haiku-4-5-20251001`** (latest Haiku snapshot — pinning
to the dated version avoids silent behaviour changes when Anthropic releases
updates).

⚠️ **Haiku + multi-turn-only is the risky combo.** Haiku is the cheapest model
but sometimes skips tool-call steps or re-calls tools it just called. The
mitigation is a tight system prompt with explicit ordering. If Haiku misbehaves
in Phase 6 testing, the **single-line fallback** is to change the model string
to `"claude-sonnet-4-6"` in `agent_utils.build_anthropic_chat_client()`.

## File layout

```
story_tools/                              ← NEW package
  __init__.py                             ← re-exports public surface
  _actions.py                             ← plain Python functions (REST, xlsx)
  _tools.py                               ← @tool wrappers around _actions
  _agent.py                               ← Agent factory + SYSTEM_PROMPT
  _secrets.py                             ← Key Vault fetch helper
  __main__.py                             ← CLI entry: python -m story_tools
story_automation.py                       ← KEEP: v1 CLI untouched
agent_utils.py                            ← EXTEND: add build_anthropic_chat_client()
.env                                      ← ADD: AZURE_KEYVAULT_URL, ANTHROPIC_KEY_SECRET_NAME
docs/
  story_automation.md                     ← KEEP: v1 spec
  story_automation_agent_plan.md          ← THIS FILE
.claude/skills/story-automation/SKILL.md  ← UPDATE: point at v2 entry
requirements.txt                          ← ADD: azure-keyvault-secrets, openpyxl
```

## Implementation phases

Each phase is small enough to test in isolation. Don't move to the next phase
until the current one passes its acceptance check.

### Phase 0 — Prep (~20 min)

1. Install deps:
   ```powershell
   pip install azure-keyvault-secrets openpyxl
   ```
2. Add to `.env`:
   ```
   AZURE_KEYVAULT_URL=https://<your-vault>.vault.azure.net
   ANTHROPIC_KEY_SECRET_NAME=<secret-name-in-vault>
   ```
3. Confirm your `AzureCliCredential` (the `az login` you already use for
   Foundry) has **Key Vault Secrets User** role on the vault. Without this
   role the fetch returns 403 even with a valid login.
4. Smoke-test the fetch:
   ```powershell
   python -c "
   from azure.identity import AzureCliCredential
   from azure.keyvault.secrets import SecretClient
   import os
   from dotenv import load_dotenv
   load_dotenv()
   client = SecretClient(os.environ['AZURE_KEYVAULT_URL'], AzureCliCredential())
   secret = client.get_secret(os.environ['ANTHROPIC_KEY_SECRET_NAME'])
   print(f'ok, len={len(secret.value)}')"
   ```

**Acceptance:** prints `ok, len=N` where N is roughly 80–110.

---

### Phase 1 — Extract reusable action functions (~30 min)

Pure refactor. Move the three core functions out of `story_automation.py` into
`story_tools/_actions.py`. Rename for clarity and add type hints:

```python
# story_tools/_actions.py
def load_stories_from_xlsx(path: str) -> list[dict]: ...
def list_dry_run_summary(rows: list[dict]) -> dict: ...
def ensure_epic_on_board(epic_name: str, cache: dict[str, int]) -> int: ...
def create_story_on_board(row: dict, epic_id: int) -> int: ...
```

Move the REST helpers (`_create_work_item`, auth setup) along with them.
Update `story_automation.py` to import from `story_tools._actions` so v1
still runs unchanged from the user's point of view.

**Acceptance:** `python story_automation.py test_stories.xlsx --dry-run` still
prints the same output as before. Pure structural change.

---

### Phase 2 — Key Vault secret fetch helper (~15 min)

```python
# story_tools/_secrets.py
import os
from azure.identity import AzureCliCredential
from azure.keyvault.secrets import SecretClient

def get_anthropic_api_key() -> str:
    """Fetch the Anthropic API key from Azure Key Vault.

    Requires AZURE_KEYVAULT_URL and ANTHROPIC_KEY_SECRET_NAME in env, and
    `az login` performed by the user with Key Vault Secrets User role.
    Cached for the process lifetime so we only call Key Vault once.
    """
    if hasattr(get_anthropic_api_key, "_cached"):
        return get_anthropic_api_key._cached
    client = SecretClient(
        vault_url=os.environ["AZURE_KEYVAULT_URL"],
        credential=AzureCliCredential(),
    )
    secret = client.get_secret(os.environ["ANTHROPIC_KEY_SECRET_NAME"])
    get_anthropic_api_key._cached = secret.value
    return secret.value
```

**Acceptance:** `python -c "from story_tools._secrets import
get_anthropic_api_key; print(len(get_anthropic_api_key()))"` prints the key
length without errors.

---

### Phase 3 — Anthropic chat client helper (~15 min)

Extend `agent_utils.py`:

```python
from agent_framework_anthropic import AnthropicClient
from story_tools._secrets import get_anthropic_api_key

def build_anthropic_chat_client(model: str = "claude-haiku-4-5-20251001") -> AnthropicClient:
    """Anthropic Claude client. API key fetched from Azure Key Vault."""
    return AnthropicClient(
        api_key=get_anthropic_api_key(),
        model=model,
    )
```

**Acceptance:** smoke-test in a one-liner —
```powershell
python -c "import asyncio; from agent_framework import Agent; from agent_utils import build_anthropic_chat_client; a = Agent(client=build_anthropic_chat_client(), instructions='Reply with exactly: ok'); print(asyncio.run(a.run('hi')))"
```
should print `ok`. Proves auth + client wiring before we add tools.

---

### Phase 4 — Wrap actions as `@tool` (~30 min)

In `story_tools/_tools.py`:

```python
from agent_framework import tool
from . import _actions

# Module-level cache so the LLM can't accidentally create duplicate Epics
# across multiple tool calls in the same conversation.
_epic_cache: dict[str, int] = {}

@tool(approval_mode="never_require")
def read_stories(path: str) -> list[dict]:
    """Read an xlsx file of Epic/Story rows and return the parsed list.

    Always call this first. Returns one dict per row with keys:
    EPIC, FEATURE, STORY, STORY TITLE, DESCRIPTION,
    ACCEPTANCE CRITERIA, STORYPOINTS, PRIORITY.
    """
    return _actions.load_stories_from_xlsx(path)

@tool(approval_mode="never_require")
def dry_run_summary(rows: list[dict]) -> dict:
    """Return counts of unique Epics, Features, and Story rows.
    Use this to show the user what would be created before any write.
    Returns: {epic_count, feature_count, story_count,
              epics: [...], features: [...]}.
    """
    return _actions.list_dry_run_summary(rows)

@tool(approval_mode="never_require")
def create_epic(epic_name: str) -> int:
    """Create (or return the cached id for) an Epic on Azure DevOps.
    Dedupes within this process via an internal cache.
    Only call this after the user has explicitly approved the dry-run.
    """
    return _actions.ensure_epic_on_board(epic_name, _epic_cache)

@tool(approval_mode="never_require")
def create_story(row: dict, epic_id: int) -> int:
    """Create a single Story (as an Issue) parented to the given Epic.
    Returns the created work item id.
    Only call this after the user has explicitly approved the dry-run.
    """
    return _actions.create_story_on_board(row, epic_id)
```

Notes:
- All four tools are `approval_mode="never_require"` because we chose
  multi-turn session as the gate, not per-tool approval.
- The Epic cache is module-level so dedupe survives across tool calls in one
  session.
- Docstrings are critical — they are the tool schema the LLM reads. Each
  docstring includes both *what* the tool does and *when* the LLM should
  call it.

**Acceptance:** print the tool list at startup; descriptions should match
the docstrings.

---

### Phase 5 — System prompt (Anthropic standards) (~45 min)

In `story_tools/_agent.py`:

```xml
SYSTEM_PROMPT = """\
<role>
You are StoryAutomationAgent, a careful release-engineering assistant. Your
only job is to upload Epic and Story work items to Azure DevOps from an xlsx
spreadsheet, using the tools provided.
</role>

<context>
Mistakes are expensive to undo, so you always validate and confirm before
writing. The target project uses the Basic process: only Epic and Issue
work-item types exist. Stories are created as Issues. Features become tags
on Stories.
</context>

<workflow>
Phase A — Inspect (do this on every fresh request)
1. Call read_stories(path) with the xlsx path the user named.
2. Call dry_run_summary(rows) on the returned rows.
3. Present the counts to the user in a short summary and ask:
   "Proceed with the real upload?"
4. STOP. Do not call create_epic or create_story yet.

Phase B — Apply (only after the user replies "yes", "go ahead", "proceed",
or similar affirmative)
5. Group rows by EPIC value.
6. For each unique Epic name, call create_epic(name) ONCE.
7. For each row, call create_story(row, epic_id_from_step_6).
8. Report the created work item ids in the table format shown below.
</workflow>

<rules>
- NEVER call create_epic or create_story before the user has affirmatively
  approved the dry-run summary you showed them.
- NEVER skip the dry-run, even if the user says "just do it" — show the
  summary and ask once.
- NEVER call create_epic more than once for the same Epic name in a session.
- Surface every Azure DevOps error verbatim. Do not retry. Do not summarise.
- If a required env var is missing and a tool raises, stop and tell the
  user which variable to set.
- Stick to the tools provided. Do not invent tool names.
</rules>

<output_format>
When reporting created items, use this exact markdown table format:

| Type  | Title                  | Id  |
|-------|------------------------|-----|
| Epic  | <epic name>            | #N  |
| Story | <story title>          | #N  |
</output_format>
"""
```

Then the factory:

```python
from agent_framework import Agent
from agent_utils import build_anthropic_chat_client
from ._tools import read_stories, dry_run_summary, create_epic, create_story

def build_agent() -> Agent:
    return Agent(
        client=build_anthropic_chat_client(),
        name="StoryAutomationAgent",
        instructions=SYSTEM_PROMPT,
        tools=[read_stories, dry_run_summary, create_epic, create_story],
    )
```

**Acceptance:** `await agent.run("Use test_stories.xlsx")` — Haiku should call
`read_stories` then `dry_run_summary`, print counts, then stop and ask.

---

### Phase 6 — Multi-turn session driver (~30 min)

In `story_tools/__main__.py`:

```python
import asyncio
from ._agent import build_agent

async def main():
    agent = build_agent()
    session = agent.create_session()

    print("StoryAutomationAgent ready. Tell me which xlsx to upload (or 'quit').")
    while True:
        user_input = input("you> ").strip()
        if user_input.lower() in {"quit", "exit"}:
            break
        result = await agent.run(user_input, session=session)
        print(f"\nagent> {result}\n")

if __name__ == "__main__":
    asyncio.run(main())
```

Run with:
```powershell
PYTHONIOENCODING=utf-8 python -m story_tools
```

A realistic transcript:

```
you> Upload test_stories.xlsx
agent> Loaded 3 rows. Would create 1 Epic ('Drug Search Platform'), tag with
       2 Features (FDA Catalog, Query UI), and create 3 Stories.
       Proceed with the real upload?
you> yes
agent> | Type  | Title                              | Id  |
       |-------|------------------------------------|-----|
       | Epic  | Drug Search Platform               | #N  |
       | Story | Build clean FDA drug catalog       | #N  |
       | Story | Add sponsor name normalization     | #N  |
       | Story | Build natural-language search box  | #N  |
```

**Acceptance:** transcript above (or close to it) runs against your real
AzureBoardTest project with no manual intervention beyond typing `yes`.

---

### Phase 7 — Update Claude Code skill (~15 min)

Edit `.claude/skills/story-automation/SKILL.md` so `/story-automation` points
at v2:

- Replace the `python story_automation.py ...` Bash invocation with
  `python -m story_tools` and a piped command driving the conversation.
- Update the description to mention "uses Claude + agent_framework".

**Acceptance:** `/story-automation test_stories.xlsx` still works end-to-end.

## Claude prompt-engineering checklist

Audit every prompt you write against this:

- [ ] Has an explicit `<role>` tag with one-sentence role definition.
- [ ] Uses XML tags for distinct sections — Claude attends to these strongly.
- [ ] States the workflow as numbered steps, not a paragraph.
- [ ] States explicit STOP / NEVER instructions for known failure modes.
- [ ] States the exact output format with an example.
- [ ] Spells out tool names, file paths, env var names — no jargon shorthand.
- [ ] Does not include irrelevant context that wastes tokens.
- [ ] Is short enough that the user can read and reason about it.

## Testing strategy

| Layer | How |
|---|---|
| `_actions.py` | Plain pytest; mock `requests`. |
| `_secrets.py` | Smoke-test from Phase 0. Real Key Vault call; no mocking needed for now. |
| `_tools.py` | Print tool list; eyeball schemas. |
| `_agent.py` (no tools) | `await agent.run("ping")` — confirms client wiring. |
| `_agent.py` (read-only) | "Show me the dry-run for test_stories.xlsx" — verify it stops after summary. |
| End-to-end | Real run against AzureBoardTest via `python -m story_tools`. |

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Haiku calls `create_story` before user approves | System prompt has explicit STOP after Phase A. If it still misbehaves in Phase 6, swap model to Sonnet (one line) or switch to per-tool approval. |
| Haiku creates duplicate Epics | Module-level `_epic_cache` in `_tools.py` returns the existing id for repeat names. |
| Haiku hallucinates column names | `read_stories` validates headers and raises before the LLM continues. |
| Key Vault permission denied | Phase 0 smoke test catches this before the agent is ever built. |
| Anthropic rate limit | Haiku has higher limits than other tiers; for 20-row sheets we'll never hit them. |
| Cost creep | Haiku is ~$0.80/M input. A 20-row sheet run costs fractions of a cent. |

## Rollback plan

v1 (`story_automation.py`) stays in place untouched. If v2 misbehaves, the
slash command can be reverted to point at v1 in one edit. No data on the
board is at risk because every write goes through the multi-turn confirmation.

## Remaining info needed before I can execute

I need two pieces of information from you before I can build Phase 0 and 2:

1. **Azure Key Vault URL** — e.g. `https://my-prod-vault.vault.azure.net`.
2. **Anthropic key secret name** — the name under which the Anthropic API
   key is stored in that vault (e.g. `anthropic-api-key`).

Optional but helpful:
3. Has the secret actually been stored in the vault yet? If not, I'll include
   the `az keyvault secret set` command you need to run first.
