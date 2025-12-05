import streamlit as st
import json

# Initialize editable storage for requirements
if "edited_requirements" not in st.session_state:
    st.session_state.edited_requirements = {}

# Load pipeline result from session
result = st.session_state.get("pipeline_result")

st.title("📘 Generated Requirements")

if not result:
    st.warning("Please upload and process a transcript first.")
    st.stop()

planner_output = result.get("planner_output", {})
epics = planner_output.get("epics", [])

# Display context
with st.expander("ℹ️ Context"):
    st.json(planner_output.get("context", {}))

st.subheader("📌 Epics & Stories")

for epic in epics:
    with st.expander(f"🟦 Epic: {epic['title']}"):
        # Unique key for this epic
        epic_key = f"epic_{epic['id']}"

        # Initialize or load existing edits
        edited_epic = st.session_state.edited_requirements.get(epic_key, {
            "title": epic["title"],
            "description": epic.get("description", ""),
            "priority": epic.get("priority", "Medium"),
            "labels": epic.get("labels", [])
        })

        st.markdown("### ✏️ Edit Epic Details")

        # Editable Title
        edited_epic_title = st.text_input(
            "Epic Title", value=edited_epic["title"], key=f"epic_title_{epic_key}"
        )

        # Editable Description
        edited_epic_desc = st.text_area(
            "Epic Description", value=edited_epic["description"], height=120,
            key=f"epic_desc_{epic_key}"
        )

        # Editable Priority
        edited_epic_priority = st.selectbox(
            "Priority",
            ["High", "Medium", "Low"],
            index=["High", "Medium", "Low"].index(edited_epic.get("priority", "Medium")),
            key=f"epic_priority_{epic_key}"
        )

        # Editable Labels
        st.write("**Labels:**")

        edited_epic_labels = edited_epic.get("labels", [])

        # Render labels with delete buttons
        for i, label in enumerate(edited_epic_labels):
            cols = st.columns([6, 1])
            edited_epic_labels[i] = cols[0].text_input(
                f"Label {i+1}", value=label, key=f"epic_label_{epic_key}_{i}"
            )
            if cols[1].button("❌", key=f"del_epic_label_{epic_key}_{i}"):
                edited_epic_labels.pop(i)
                st.rerun()

        # Add new label
        if st.button("➕ Add Label", key=f"add_epic_label_{epic_key}"):
            edited_epic_labels.append("")
            st.rerun()

        # SAVE BUTTON FOR EPIC
        if st.button("💾 Save Epic", key=f"save_epic_{epic_key}"):
            st.session_state.edited_requirements[epic_key] = {
                "title": edited_epic_title,
                "description": edited_epic_desc,
                "priority": edited_epic_priority,
                "labels": edited_epic_labels
            }
            st.success("Epic saved!")

        stories = epic.get("stories", [])
        st.markdown("---")

        if not stories:
            st.info("No stories were generated for this epic.")
            continue

        st.write("### Stories")

        # Render each story block
        for story in stories:

            story_key = f"{epic['id']}_{story['id']}"

            with st.expander(f"📝 {story['id']} — {story['title']}"):

                # Load existing edits or original story
                edited = st.session_state.edited_requirements.get(story_key, {
                    "title": story["title"],
                    "description": story["description"],
                    "acceptance_criteria": story.get("acceptance_criteria", [])
                })

                # ---------------------------
                # Editable TITLE
                # ---------------------------
                edited_title = st.text_input(
                    "Title", value=edited["title"], key=f"title_{story_key}"
                )

                # ---------------------------
                # Editable DESCRIPTION
                # ---------------------------
                edited_desc = st.text_area(
                    "Description", value=edited["description"],
                    height=130, key=f"desc_{story_key}"
                )

                # ---------------------------
                # Editable ACCEPTANCE CRITERIA
                # ---------------------------
                st.write("**Acceptance Criteria:**")

                edited_ac_list = edited["acceptance_criteria"]

                # Render each AC item with delete button
                for i, ac in enumerate(edited_ac_list):
                    cols = st.columns([6, 1])
                    edited_ac_list[i] = cols[0].text_input(
                        f"AC {i+1}", value=ac,
                        key=f"ac_{story_key}_{i}"
                    )

                    if cols[1].button("❌", key=f"del_ac_{story_key}_{i}"):
                        edited_ac_list.pop(i)
                        st.rerun()

                # Add new AC
                if st.button("➕ Add Acceptance Criterion", key=f"add_ac_{story_key}"):
                    edited_ac_list.append("")
                    st.rerun()

                # ---------------------------
                # SAVE button
                # ---------------------------
                if st.button("💾 Save Changes", key=f"save_{story_key}"):
                    st.session_state.edited_requirements[story_key] = {
                        "title": edited_title,
                        "description": edited_desc,
                        "acceptance_criteria": edited_ac_list
                    }
                    st.success("Saved!")
