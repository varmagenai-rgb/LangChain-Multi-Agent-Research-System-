"""@tool wrappers over story_tools._actions for use by an Agent.

The docstrings here ARE the tool schemas the LLM reads to decide when to call
each tool. Keep them concrete and ordering-aware.
"""

from agent_framework import tool

from . import _actions

# Module-level cache: dedupes Epics across tool calls within one Agent session.
# The agent has no concept of "I already created this", so we enforce it here.
_epic_cache: dict[str, int] = {}


@tool(approval_mode="never_require")
def read_stories(path: str) -> list[dict]:
    """Read an xlsx file of Epic/Story rows and return the parsed list.

    ALWAYS call this first when the user names an xlsx file.
    Each returned dict has these keys:
        EPIC, FEATURE, STORY, STORY TITLE, DESCRIPTION,
        ACCEPTANCE CRITERIA, STORYPOINTS, PRIORITY.

    Raises ValueError if any required header is missing.
    """
    return _actions.load_stories_from_xlsx(path)


@tool(approval_mode="never_require")
def dry_run_summary(rows: list[dict]) -> dict:
    """Summarise what would be created. Does NOT touch Azure DevOps.

    Always call this after read_stories and show the result to the user
    before any create_* call.

    Returns:
        {
          "epic_count":    int,
          "feature_count": int,
          "story_count":   int,
          "epics":         list[str],
          "features":      list[str],
        }
    """
    return _actions.list_dry_run_summary(rows)


@tool(approval_mode="never_require")
def create_epic(epic_name: str) -> int:
    """Create an Epic work item on Azure DevOps and return its id.

    Dedupes via an internal cache: calling this twice with the same name
    in one process returns the same id without a second REST call.

    Only call AFTER the user has explicitly approved the dry-run summary
    (replies with "yes", "go ahead", "proceed", or similar).
    """
    return _actions.ensure_epic_on_board(epic_name, _epic_cache)


@tool(approval_mode="never_require")
def create_story(row: dict, epic_id: int) -> int:
    """Create one Story (as an Issue) parented to the given Epic id.

    Only call AFTER the user has approved the dry-run AND after create_epic
    has been called for the row's EPIC value.

    `row` is a dict matching the row_schema described in the system prompt.
    It may come from read_stories (FILE mode) or be constructed by you from
    the user's chat description (CHAT mode). Required keys: STORY TITLE.
    Optional keys: EPIC, FEATURE, STORY, DESCRIPTION, ACCEPTANCE CRITERIA,
    STORYPOINTS, PRIORITY. Use null or "" for fields the user did not give.

    `epic_id` must be the value returned by a prior create_epic call.
    """
    return _actions.create_story_on_board(row, epic_id)


def reset_epic_cache() -> None:
    """Clear the in-process Epic dedupe cache. Useful between independent runs."""
    _epic_cache.clear()
