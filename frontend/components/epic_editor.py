import streamlit as st

def render_epic_editor(epic):
    with st.expander(f"📌 {epic['epic_name']}", expanded=False):
        epic_name = st.text_input("Epic Name", epic["epic_name"])
        description = st.text_area("Description", epic["description"])

        stories = []
        st.write("### User Stories")
        for story in epic["user_stories"]:
            with st.container():
                story_desc = st.text_area(
                    f"Story {story['id']}",
                    story["description"]
                )
                ac = st.text_area(
                    f"Acceptance Criteria {story['id']}",
                    "\n".join(story["acceptance_criteria"])
                )
                stories.append({
                    "id": story["id"],
                    "description": story_desc,
                    "acceptance_criteria": ac.split("\n")
                })

        return {
            "epic_name": epic_name,
            "description": description,
            "user_stories": stories
        }
