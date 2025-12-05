# backend/agents/reviewer.py

import json
from backend.llm.llm_client import LLMClient
from backend.utils import prompts

import re

def extract_json_block(text: str) -> str:
    """
    Extracts the largest valid JSON block from LLM output.
    Finds the first '{' and last '}', returns substring.
    This is extremely robust for imperfect LLM outputs.
    """
    try:
        start = text.index("{")
        end = text.rindex("}")
        return text[start:end+1]
    except:
        raise ValueError(f"Could not extract JSON block from reviewer output:\n{text[:500]}")

def clean_json_output(raw_text: str) -> str:
    """
    Removes ```json fences and extracts the JSON content.
    """
    cleaned = re.sub(r"```json", "", raw_text, flags=re.IGNORECASE)
    cleaned = re.sub(r"```", "", cleaned)
    return cleaned.strip()


class ReviewerAgent:

    def __init__(self, model: str = "mistral-small-latest"):
        self.llm = LLMClient(model=model)

    def review_requirements(self, planner_json: dict):
        """
        Sends planner output to Mistral for review.
        Returns parsed JSON.
        """

        # System prompt
        system_prompt = prompts.SYSTEM_REVIEWER + "\n\n" + prompts.REVIEWER_FEW_SHOT

        # Convert planner JSON to string
        planner_json_str = json.dumps(planner_json, indent=2)

        # Build user prompt
        user_prompt = prompts.REVIEWER_PROMPT + "\n\nHERE IS THE INPUT:\n" + planner_json_str

        # Call Mistral
        raw_output = self.llm.chat(
            system=system_prompt,
            user=user_prompt,
            temperature=0.0,
            max_tokens=800
        )

        # Clean up Markdown
        cleaned = clean_json_output(raw_output)

        # Final safety: truncate anything after last closing brace
        #last_brace = cleaned.rfind("}")
        #cleaned = cleaned[: last_brace + 1]
        json_block = extract_json_block(cleaned)

        try:
            parsed = json.loads(json_block)
        except Exception as e:
            raise ValueError(f"Reviewer JSON parse failed: {e}\nRAW JSON BLOCK:\n{json_block}")

        
        # Parse JSON
        #try:
        #    parsed = json.loads(cleaned)
        #except Exception as e:
        #    raise ValueError(f"Reviewer output not valid JSON: {e}\nRAW:\n{raw_output}")

        return parsed
