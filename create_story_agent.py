# create_story_agent.py

import os
import requests
import json
import base64
import re

from dotenv import load_dotenv

load_dotenv()

# ─── CONFIG ───────────────────────────────────────────
ORG        = os.environ["AZURE_DEVOPS_ORG"]
PROJECT    = os.environ["AZURE_DEVOPS_PROJECT"]
PAT        = os.environ["AZURE_DEVOPS_PAT"]
AREA       = os.environ["AZURE_DEVOPS_AREA_PATH"]
ITERATION  = os.environ["AZURE_DEVOPS_ITERATION_PATH"]
REVIEWER   = os.environ["AZURE_DEVOPS_REVIEWER"]
DOC_BASE   = "main/LangChain-Multi-Agent-Research-System-/docs"

token   = base64.b64encode(f":{PAT}".encode()).decode()
HEADERS = {
    "Content-Type": "application/json-patch+json",
    "Authorization": f"Basic {token}"
}

# ─── STEP 1: CREATE USER STORY ────────────────────────
def create_user_story(title, summary, as_a, i_want, so_that,
                       business_value, measurable_outcome,
                       acceptance_criteria, story_points=5, priority=1, tags=""):

    url = (f"https://dev.azure.com/{ORG}/{PROJECT}/"
           f"_apis/wit/workitems/$Issue?api-version=7.0")

    ac_html = "<ol>" + "".join(
        f"<li>{c.strip()}</li>"
        for c in acceptance_criteria.split("\n") if c.strip()
    ) + "</ol>"

    description = f"""
    <b>Summary:</b> {summary}<br><br>
    <b>As a</b> {as_a}<br>
    <b>I want</b> {i_want}<br>
    <b>So that</b> {so_that}<br><br>
    <b>Business Value:</b> {business_value}<br><br>
    <b>Measurable outcome:</b> {measurable_outcome}<br><br>
    <b>Acceptance Reviewer:</b> {REVIEWER}<br><br>
    <b>Acceptance Criteria:</b>{ac_html}
    """

    payload = [
        {"op": "add", "path": "/fields/System.Title",           "value": title},
        {"op": "add", "path": "/fields/System.Description",     "value": description},
        {"op": "add", "path": "/fields/System.AreaPath",        "value": AREA},
        {"op": "add", "path": "/fields/System.IterationPath",   "value": ITERATION},
        {"op": "add", "path": "/fields/Microsoft.VSTS.Scheduling.Effort", "value": story_points},
        {"op": "add", "path": "/fields/Microsoft.VSTS.Common.Priority", "value": priority},
        {"op": "add", "path": "/fields/System.Tags",            "value": tags},
    ]

    res = requests.post(url, headers=HEADERS, data=json.dumps(payload))
    if not res.ok:
        print(f"❌ Azure DevOps returned {res.status_code}: {res.text}")
        res.raise_for_status()
    story = res.json()
    story_id = story["id"]
    print(f"✅ User Story Created → ID: {story_id} | {title}")
    return story_id


# ─── STEP 2: CREATE CHILD TASKS ──────────────────────
def create_child_task(parent_id, task_title, story_id_prefix):
    url = (f"https://dev.azure.com/{ORG}/{PROJECT}/"
           f"_apis/wit/workitems/$Task?api-version=7.0")

    payload = [
        {"op": "add", "path": "/fields/System.Title",         "value": task_title},
        {"op": "add", "path": "/fields/System.AreaPath",      "value": AREA},
        {"op": "add", "path": "/fields/System.IterationPath", "value": ITERATION},
        {"op": "add", "path": "/relations/-", "value": {
            "rel": "System.LinkTypes.Hierarchy-Reverse",
            "url": (f"https://dev.azure.com/{ORG}/{PROJECT}/"
                    f"_apis/wit/workitems/{parent_id}")
        }}
    ]

    res = requests.post(url, headers=HEADERS, data=json.dumps(payload))
    task = res.json()
    print(f"   ↳ Task Created → ID: {task['id']} | {task_title}")
    return task["id"]


# ─── STEP 3: GENERATE MARKDOWN FILE ──────────────────
def generate_markdown(story_id, title, summary, as_a, i_want,
                       so_that, business_value, measurable_outcome,
                       acceptance_criteria):

    safe_title = re.sub(r"[^a-zA-Z0-9]+", "_", title)
    doc_path   = f"{DOC_BASE}/US-{story_id}_{safe_title}.md"

    content = f"""# US-{story_id} – {title}

## Overview
{summary}

## User Story
**As a** {as_a}
**I want** {i_want}
**So that** {so_that}

## Business Value
{business_value}

## Measurable Outcome
{measurable_outcome}

## Acceptance Criteria
{acceptance_criteria}

## References
- [Azure Board – Work Item {story_id}](https://dev.azure.com/{ORG}/{PROJECT}/_workitems/edit/{story_id})

## Status
- [ ] In Progress
- [ ] In Review  
- [ ] Done
"""

    # Save locally
    filename = f"US-{story_id}_{safe_title}.md"
    with open(filename, "w") as f:
        f.write(content)

    print(f"📄 Markdown saved → {filename}")
    print(f"📁 Commit to: {doc_path}")
    return filename, doc_path


# ─── STEP 4: UPDATE STORY WITH DOC PATH ──────────────
def update_story_doc_path(story_id, doc_path):
    url = (f"https://dev.azure.com/{ORG}/{PROJECT}/"
           f"_apis/wit/workitems/{story_id}?api-version=7.0")

    payload = [{
        "op": "add",
        "path": "/fields/System.Description",
        "value": f"<b>Detailed build plan:</b> {doc_path}"
    }]

    requests.patch(url, headers=HEADERS, data=json.dumps(payload))
    print(f"🔗 Doc path linked back to Work Item {story_id}")


# ─── MAIN RUNNER ─────────────────────────────────────
def run_story_automation(story_data):
    print("\n🚀 Starting Story Automation...\n")

    # 1. Create User Story
    story_id = create_user_story(**story_data)

    # 2. Create Child Tasks (matching your T1–T6 pattern)
    tasks = [
        f"T1: Create {story_data['title']} Tables in DB",
        f"T2: Deploy Pilot Data",
        f"T3: Backfill Full Dataset",
        f"T4: Build Stored Procedures",
        f"T5: Run Killer Test on {story_data['title']}",
        f"T6: Write Completion Docs",
    ]
    for task in tasks:
        create_child_task(story_id, task, story_id)

    # 3. Generate Markdown
    filename, doc_path = generate_markdown(story_id, **{
        k: story_data[k] for k in [
            "title", "summary", "as_a", "i_want", "so_that",
            "business_value", "measurable_outcome", "acceptance_criteria"
        ]
    })

    # 4. Link doc path back
    update_story_doc_path(story_id, doc_path)

    print(f"\n✅ Done! Story #{story_id} created with {len(tasks)} tasks & markdown doc.\n")


# ─── EXAMPLE USAGE ───────────────────────────────────
story_input = {
    "title":                "FDA Catalog for Faster, Accurate Drug Search",
    "summary":              "Replace broken nephrology drug search returning ~28,000 unrelated rows with clean indexed FDA catalog",
    "as_a":                 "Chief Medical Officer or regulatory analyst",
    "i_want":               "'show nephrology drugs' to return only true nephrology drugs",
    "so_that":              "I can trust the results and finish a drug review in one sitting",
    "business_value":       "CMOs lose time filtering and lose trust in the system. Fixing this delivers a credible single-question demo",
    "measurable_outcome":   "Primary_Therapeutic_Area = Nephrology returns <= 15 rows, down from ~28,000 today",
    "acceptance_criteria":  """Filtering by Nephrology returns Kerendia and excludes dexamethasone
Searching for sponsor Pfizer matches all Pfizer entity variants
Year-range filter returns only drugs approved in that range
All 54,186 FDA labels appear in the catalog
Single filter query returns in under 100 milliseconds""",
    "story_points":         5,
    "priority":             1,
    "tags":                 "accuracy, backend, catalog, FDA, sprint-59"
}

run_story_automation(story_input)