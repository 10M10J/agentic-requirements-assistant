# backend/agents/pipeline.py

from backend.agents.planner import PlannerAgent
from backend.agents.reviewer import ReviewerAgent
from backend.agents.story_generator import StoryGeneratorAgent

class RequirementsPipeline:

    def __init__(self, model="mistral-small-latest"):
        self.planner = PlannerAgent(model)
        self.story_gen = StoryGeneratorAgent(model)
        self.reviewer = ReviewerAgent(model)

    def run(self, transcript: str):
        """
        Runs:
         1. Planner Agent
         2. Reviewer Agent
        and returns combined output.
        """

        # Step 1: Generate requirements (epics/stories)
        planner_output = self.planner.generate_requirements(transcript)

        # NEW STEP 2: Generate stories for each epic
        for epic in planner_output["epics"]:
            if "user_stories" in epic:
                del epic["user_stories"]
            epic_title = epic.get("title")
            epic_desc = epic.get("description")

            generated_stories = self.story_gen.generate_stories_for_epic(
                epic_title,
                epic_desc
            )

            # Overwrite empty stories[] with generated stories
            epic["stories"] = generated_stories

        # Step 3: Review generated requirements
        reviewer_output = self.reviewer.review_requirements(planner_output)

        return {
            "planner_output": planner_output,
            "reviewer_output": reviewer_output
        }
