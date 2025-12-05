# frontend/pages/3_Review_and_Approve.py
import streamlit as st
import json
import copy
import requests
from streamlit import session_state as ss
from backend.jira.jira_client import JiraClient

st.title("📝 Review & Approve Requirements")

# Preconditions
if "pipeline_result" not in st.session_state:
    st.warning("Please upload and process a transcript first.")
    st.stop()

# Initialize approvals store
if "approvals" not in st.session_state:
    st.session_state.approvals = {}

# Helper callbacks for checkbox behavior
def toggle_epic(epic_key, story_keys):
    """When epic checkbox toggled, toggle all stories to same value."""
    epic_checkbox_key = f"approve_{epic_key}"
    new_val = st.session_state.get(epic_checkbox_key, False)
    # ensure approvals mapping exists
    st.session_state.approvals[epic_key] = new_val
    for sk in story_keys:
        st.session_state.approvals[sk] = new_val
        st.session_state[f"approve_{sk}"] = new_val
    st.rerun()

def toggle_story(epic_key, story_key, story_keys):
    """When a story checkbox toggled, update epic based on story states."""
    story_checkbox_key = f"approve_{story_key}"
    new_val = st.session_state.get(story_checkbox_key, False)

    st.session_state.approvals[story_key] = new_val

    epic_checkbox_key = f"approve_{epic_key}"

    # FUTURE STATE: check how many stories are approved
    approved_stories = [
        st.session_state.get(f"approve_{sk}", False) 
        for sk in story_keys
    ]

    if any(approved_stories):
        # At least ONE story approved → epic must be approved
        st.session_state.approvals[epic_key] = True
        st.session_state[epic_checkbox_key] = True
    else:
        # No approved stories → epic must be unapproved
        st.session_state.approvals[epic_key] = False
        st.session_state[epic_checkbox_key] = False

    st.rerun()

# Read planner + edited items
planner_output = st.session_state.pipeline_result.get("planner_output", {})
edited_items = st.session_state.get("edited_requirements", {})

st.info("Only the epics and stories you approve (checked) will be updated in JIRA. Use the checkboxes below to select what you want to push.")

final_output = copy.deepcopy(planner_output)

# UI: iterate epics similar to Generated Requirements page
for epic in final_output.get("epics", []):
    epic_key = f"epic_{epic['id']}"

    # Apply any epic edits (if saved)
    if epic_key in edited_items:
        updates = edited_items[epic_key]
        epic["title"] = updates.get("title", epic["title"])
        epic["description"] = updates.get("description", epic.get("description", ""))
        epic["priority"] = updates.get("priority", epic.get("priority", "Medium"))
        epic["labels"] = updates.get("labels", epic.get("labels", []))

    # Prepare list of story keys for callbacks
    story_keys = []
    for s in epic.get("stories", []):
        story_keys.append(f"{epic['id']}_{s['id']}")

    # Initialize approval states if missing
    if epic_key not in st.session_state.approvals:
        st.session_state.approvals[epic_key] = False
    for sk in story_keys:
        if sk not in st.session_state.approvals:
            st.session_state.approvals[sk] = False

    # Ensure checkbox widgets are present with callback binding
    with st.expander(f"🟦 Epic: {epic['title']}"):
        st.write(f"**ID:** {epic.get('id')}")
        st.write(f"**Description:** {epic.get('description')}")
        st.write(f"**Priority:** {epic.get('priority', 'Medium')}")
        st.write(f"**Labels:** {', '.join(epic.get('labels', []))}")

        # Epic checkbox (on_change triggers toggle_epic)
        st.checkbox(
            "✔ Approve Epic",
            value=st.session_state.approvals[epic_key],
            key=f"approve_{epic_key}",
            on_change=toggle_epic,
            args=(epic_key, story_keys)
        )

        st.markdown("---")
        st.write("### Stories")

        # Stories
        for story in epic.get("stories", []):
            story_key = f"{epic['id']}_{story['id']}"

            # Apply story edits if present
            if story_key in edited_items:
                updates = edited_items[story_key]
                story["title"] = updates.get("title", story.get("title"))
                story["description"] = updates.get("description", story.get("description"))
                story["acceptance_criteria"] = updates.get("acceptance_criteria", story.get("acceptance_criteria", []))

            # Each story expander with approval checkbox
            with st.expander(f"📝 {story['id']} — {story['title']}"):
                st.write(f"**Description:** {story.get('description','')}")
                st.write("**Acceptance Criteria:**")
                for ac in story.get("acceptance_criteria", []):
                    st.markdown(f"- {ac}")

                # Story checkbox with on_change callback to toggle_story
                st.checkbox(
                    "✔ Approve Story",
                    value=st.session_state.approvals[story_key],
                    key=f"approve_{story_key}",
                    on_change=toggle_story,
                    args=(epic_key, story_key, story_keys)
                )

# Approval summary & preview
st.markdown("---")
approved_items = [k for k, v in st.session_state.approvals.items() if v]
approved_epics = [k for k in approved_items if k.startswith("epic_")]
approved_stories = [k for k in approved_items if not k.startswith("epic_")]

st.success(f"Approved: {len(approved_epics)} epics, {len(approved_stories)} stories.")

# Preview what will be sent to JIRA (approved subset)
def build_approved_payload():
    payload = {"epics": [], "context": final_output.get("context", {})}
    for epic in final_output.get("epics", []):
        epic_key = f"epic_{epic['id']}"
        if st.session_state.approvals.get(epic_key):
            # include epic and only approved stories
            epic_copy = {
                "id": epic["id"],
                "title": epic["title"],
                "description": epic.get("description",""),
                "priority": epic.get("priority","Medium"),
                "labels": epic.get("labels", []),
                "stories": []
            }
            for s in epic.get("stories", []):
                sk = f"{epic['id']}_{s['id']}"
                if st.session_state.approvals.get(sk):
                    epic_copy["stories"].append(s)
            payload["epics"].append(epic_copy)
    return payload

if st.button("🔍 Preview Approved Payload for JIRA"):
    approved_payload = build_approved_payload()
    if not approved_payload["epics"]:
        st.warning("No approved epics/stories selected.")
    else:
        st.json(approved_payload)

# JIRA sync button
if st.button("🔁 Sync Approved Items to JIRA"):
    approved_payload = build_approved_payload()
    
    if not approved_payload["epics"]:
        st.warning("No approved epics/stories to sync.")
        st.stop()

    with st.spinner("Syncing approved items to JIRA..."):
        try:
            jira = JiraClient()
            sync_result = jira.sync_approved_payload(approved_payload)

            # Store full sync result in the session
            st.session_state["jira_sync_result"] = sync_result

            st.success("Jira sync complete!")
            st.write("Created / Reused Jira Issues:")
            st.json(sync_result)

        except Exception as e:
            st.error(f"Jira sync error: {e}")

            # ---------------------
            # SHOW CLICKABLE LINKS
            # ---------------------
            JIRA_SITE = "https://10m10j.atlassian.net"

            st.subheader("Created / Reused Jira Issues")

            jira_epics = data["result"].get("epics", [])

            for epic in jira_epics:
                epic_key = epic.get("jira_key") if isinstance(epic, dict) else epic
                epic_url = f"{JIRA_SITE}/browse/{epic_key}"

                st.markdown(f"### 🟪 Epic: [{epic_key}]({epic_url})")

                # Stories loop (fixed)
                for story in epic.get("stories", []):
                    if isinstance(story, dict):
                        story_key = story.get("jira_key")
                    else:
                        story_key = story

                    if not story_key:
                        continue

                    story_url = f"{JIRA_SITE}/browse/{story_key}"
                    st.markdown(f"- 🟩 Story: [{story_key}]({story_url})")

        except Exception as e:
            st.error(f"Jira sync error: {e}")
