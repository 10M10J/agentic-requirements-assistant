# backend/agents/story_generator.py

import json
import re
from backend.llm.llm_client import LLMClient

def clean_json_output(raw_text: str) -> str:
    cleaned = re.sub(r"```json", "", raw_text, flags=re.IGNORECASE)
    cleaned = re.sub(r"```", "", cleaned)
    return cleaned.strip()


class StoryGeneratorAgent:

    def __init__(self, model="mistral-small-latest"):
        self.llm = LLMClient(model=model)

    def generate_stories_for_epic(self, epic_title: str, epic_description: str):
        """
        Generates 3–6 stories for a given epic.
        """

        system_prompt = """
        You are a senior Agile Business Analyst. 
        You write high-quality user stories with acceptance criteria.
        Follow INVEST and best product practices.
        """

        user_prompt = f"""
Generate between 3 to 6 detailed user stories for this EPIC:

EPIC TITLE: {epic_title}
EPIC DESCRIPTION: {epic_description}

Each story MUST follow this JSON format:

{{
  "id": "string",
  "title": "string",
  "description": "string",
  "acceptance_criteria": [
     "string", "string", "string"
  ],
  "priority": "High | Medium | Low",
  "dependencies": [],
  "source_span": {{
     "start_char": 0,
     "end_char": 0
  }}
}}

Return ONLY JSON list: [ {{story1}}, {{story2}}, ... ]
"""

        raw_output = self.llm.chat(
            system=system_prompt,
            user=user_prompt,
            temperature=0.2,
            max_tokens=3000
        )

        cleaned = clean_json_output(raw_output)

        try:
            parsed = json.loads(cleaned)
        except Exception as e:
            raise ValueError(f"StoryGenerator invalid JSON: {e}\nRAW:\n{raw_output}")

        return parsed
