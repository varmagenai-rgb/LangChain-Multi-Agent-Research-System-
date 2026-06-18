"""Bulk-create Azure DevOps work items from an xlsx spreadsheet (v1 CLI).

Usage:
    python story_automation.py path/to/stories.xlsx [--dry-run] [--continue-on-error]

The reusable logic lives in `story_tools/_actions.py`. This file is just the
deterministic CLI wrapper around it. For the agent-driven version use
`python -m story_tools`.
"""

import argparse
import sys

from dotenv import load_dotenv

load_dotenv()

from story_tools._actions import (  # noqa: E402  (env must load first)
    create_story_on_board,
    ensure_epic_on_board,
    list_dry_run_summary,
    load_stories_from_xlsx,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xlsx", help="Path to the .xlsx file")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Validate and summarise; do not call Azure DevOps",
    )
    parser.add_argument(
        "--continue-on-error", action="store_true",
        help="Skip failed rows instead of stopping at first failure",
    )
    args = parser.parse_args()

    rows = load_stories_from_xlsx(args.xlsx)
    print(f"Loaded {len(rows)} rows from {args.xlsx}")

    if args.dry_run:
        summary = list_dry_run_summary(rows)
        print(f"  Would create {summary['epic_count']} Epic(s): {summary['epics']}")
        print(f"  Would tag with {summary['feature_count']} Feature(s): {summary['features']}")
        print(f"  Would create {summary['story_count']} Story Issue(s)")
        return 0

    epic_cache: dict[str, int] = {}
    failures: list[tuple[int, str]] = []
    for i, row in enumerate(rows, start=2):
        try:
            epic_id = ensure_epic_on_board(row["EPIC"], epic_cache) if row["EPIC"] else None
            if row["EPIC"] and epic_cache[row["EPIC"]] == epic_id:
                print(f"  + Epic '{row['EPIC']}' -> #{epic_id}")
            story_id = create_story_on_board(row, epic_id)
            print(f"  + Story '{row['STORY TITLE']}' -> #{story_id}")
        except Exception as e:
            print(f"  ! Row {i}: {e}")
            failures.append((i, str(e)))
            if not args.continue_on_error:
                return 1

    if failures:
        print(f"\nDone with {len(failures)} failure(s).")
        return 1
    print(f"\nDone. {len(epic_cache)} Epic(s) + {len(rows)} Story Issue(s) created.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
