import streamlit as st

def display_review(epics, review_feedback=None):
    st.subheader("📘 Final Review")

    for epic in epics:
        with st.expander(f"📌 {epic['epic_name']}", expanded=False):
            st.markdown("### Description")
            st.write(epic["description"])

            st.markdown("### User Stories")
            for story in epic["user_stories"]:
                st.markdown(f"**🔹 Story {story['id']}**")
                st.write(story["description"])

                st.markdown("**Acceptance Criteria:**")
                for ac in story["acceptance_criteria"]:
                    st.write(f"- {ac}")

    if review_feedback:
        st.subheader("🔍 Reviewer Feedback")

        if review_feedback.get("improvements"):
            st.markdown("### Improvements")
            for item in review_feedback["improvements"]:
                st.write(f"- {item}")

        if review_feedback.get("missing_items"):
            st.markdown("### Missing Items")
            for item in review_feedback["missing_items"]:
                st.write(f"- {item}")

        if review_feedback.get("suggestions"):
            st.markdown("### Suggestions")
            for item in review_feedback["suggestions"]:
                st.write(f"- {item}")
