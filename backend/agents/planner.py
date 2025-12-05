# backend/agents/planner.py

import json
from backend.llm.llm_client import LLMClient
from backend.utils import prompts
import re
import json

def clean_json_output(raw_text: str) -> str:
    """
    Removes Markdown fences (```json), extra whitespace,
    and extracts the JSON object from the LLM response.
    """
    # Remove code fences
    cleaned = re.sub(r"```json", "", raw_text, flags=re.IGNORECASE)
    cleaned = re.sub(r"```", "", cleaned)

    # Trim whitespace
    cleaned = cleaned.strip()

    return cleaned

def transform_to_nested_structure(parsed_json: dict) -> dict:
    """
    Converts output from:
      { "epics": [...], "stories": [...] }
    to:
      { "epics": [ { ... , "stories": [ ... ] } ] }
    """

    epics = parsed_json.get("epics", [])
    stories = parsed_json.get("stories", [])

    # Map each epic by id
    epic_map = {e["id"]: e for e in epics}

    # Add stories list inside each epic
    for epic in epics:
        epic["stories"] = []

    # Attach each story to its epic
    for s in stories:
        epic_id = s.get("epic_id")
        if epic_id in epic_map:
            epic_map[epic_id]["stories"].append(s)

    # Remove top-level stories key
    if "stories" in parsed_json:
        del parsed_json["stories"]

    return parsed_json

class PlannerAgent:

    def __init__(self, model: str = "mistral-small-latest"):
        self.llm = LLMClient(model=model)

    def generate_requirements(self, transcript: str):
        """
        Step 1: Build the LLM prompt for the planner agent.
        Step 2: Call Mistral.
        Step 3: Return the raw JSON (as string).
        """

        # Build system prompt
        system_prompt = prompts.SYSTEM_PLANNER.format(
            schema_reference="SCHEMA_JSON"
        )

        # Build user prompt
        user_prompt = prompts.PLANNER_PROMPT.format(
            system="",
            transcript=transcript,
            meeting_type="grooming",
            language="en",
            domain_hints="admin portal, user management, fleet management, driver module, employee attendance",
            schema_key="SCHEMA_JSON"
        )

        # Call Mistral
        raw_output = self.llm.chat(
            system=system_prompt,
            user=user_prompt,
            temperature=0.0,
            max_tokens=3000
        )

        cleaned = clean_json_output(raw_output)

        try:
            parsed = json.loads(cleaned)
        except Exception as e:
            raise ValueError(f"Planner output is not valid JSON: {e}\nRaw text:\n{raw_output}")

        # Transform to nested epics.stories[] structure (Option 2)
        nested = transform_to_nested_structure(parsed)

        return nested
    