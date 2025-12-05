# backend/utils/prompts.py
# Prompt templates and helper strings for the Agentic Requirements Assistant.
# Keep this file under version control (no secrets).
# The templates use curly-brace placeholders for substitution, e.g. {transcript} or {examples}.

# -----------------------
# SYSTEM / ROLE PROMPTS
# -----------------------
SYSTEM_PLANNER = """
You are an expert Agile product requirements generator. Your job is to read meeting transcripts or summaries,
identify meaningful epics, features, and user stories, and produce a structured, machine-readable JSON output
that a Product Owner can review and a connector agent can push into JIRA.

Requirements:
- Output must be valid JSON following the EXACT schema in {schema_reference}.
- Only produce JSON — do NOT include any explanatory text, commentary or markdown.
- If you are unsure about a field (e.g., priority), set it to null rather than guessing.
- Keep story titles concise (<= 12 words) and ensure acceptance_criteria is a short list (1–5 bullet items).
- Preserve traceability by attaching source_span (start_char, end_char) where each artifact came from in the transcript, if available.
"""

SYSTEM_REVIEWER = """
You are a Senior Agile Reviewer.
Review the quality of epics ONLY.
Do not analyze stories.
Follow the schema provided in REVIEW_SCHEMA_JSON.
"""

# -----------------------
# SCHEMA REFERENCES (human-readable; use same schema in code)
# -----------------------
SCHEMA_JSON = r"""
Schema: AnalysisOutput
{
  "metadata": {
    "transcript_source": "string",
    "processed_at": "ISO8601 timestamp",
    "model": "string",
    "confidence_overall": "float (0.0-1.0) or null"
  },
  "epics": [
    {
      "id": "string (uuid)",
      "title": "string",
      "description": "string or null",
      "priority": "string enum [highest, high, medium, low, lowest] or null",
      "stories": [
        {
          "id": "string (uuid)",
          "title": "string",
          "description": "string",
          "acceptance_criteria": ["string", ...],
          "priority": "string enum or null",
          "estimated_points": "integer or null",
          "assignee": "string or null",
          "labels": ["string", ...] or [],
          "dependencies": ["story_id", ...] or [],
          "source_span": {"start_char": int, "end_char": int} or null
        }
      ],
      "notes": "string or null"
    }
  ],
  "errors": null or ["string", ...]
}
"""

REVIEW_SCHEMA_JSON = r"""
Schema: ReviewOutput
{
  "metadata": {
    "reviewed_at": "ISO8601 timestamp",
    "reviewer_model": "string",
    "confidence_overall": "float (0.0-1.0)"
  },
  "epics": [
    {
      "id": "string (uuid)",
      "title": "string",
      "issues": [
        {
          "type": "clarity | missing_acceptance_criteria | ambiguous_scope | dependency_missing | priority_suspicious | estimate_missing",
          "severity": "info | warning | critical",
          "original": "string (original content)",
          "suggested_fix": "string",
          "confidence": "float (0.0-1.0)"
        }
      ],
      "stories": [
        {
          "id": "string (uuid)",
          "issues": [...],
          "suggested_rewrite": "string or null"
        }
      ]
    }
  ]
}
"""

# -----------------------
# PLANNER PROMPT (main extraction template)
# -----------------------
PLANNER_PROMPT = """
{system}

Transcript:
\"\"\"
{transcript}
\"\"\"

Context:
- Meeting type: {meeting_type}               # e.g., sprint_planning, grooming, design_review, retro
- Transcript language: {language}
- Business domain hints: {domain_hints}      # free text, optional

Instructions:

1) Identify ALL user needs, actions, features, improvements, flows, screens, or requirements mentioned in the transcript. No matter how high-level or vague.
2) For each major cluster of related requirements, create an EPIC. Never create fewer than 1 epic.
3) For *every* meaningful action, feature, or user intention, generate at least one USER STORY. 
   - If the transcript mentions: login, create, update, delete, view, dashboard, report, search, filter, export, manage users, assign roles, track attendance, notifications, settings, anything → CREATE a story.
4) STORIES ARE NOT OPTIONAL. Do NOT skip stories. Even if transcript is unclear, infer reasonable, generic stories based on the epic theme.
5) Each EPIC MUST have at least **3–6 stories** unless transcript is extremely short.
6) Every story MUST contain:
   - title
   - description
   - acceptance_criteria (min 3 items)
   - priority (guess if missing)
   - dependencies (guess if missing)
   - source_span (can be approximate)
7) Your job is to INFER and EXPAND. 
   - If transcript gives one line: “Admin should manage drivers”, 
     → create 3 stories automatically:
     → Create driver, Edit driver, Delete driver, View driver list.
8) Even if transcript does not mention details explicitly, generate fully fleshed-out USER STORIES based on best industry practices.
9) You MUST follow the JSON schema strictly and output valid JSON.

Produce JSON now.
"""

# -----------------------
# PLANNER FEW-SHOT EXAMPLES (short, helpful)
# -----------------------
PLANNER_FEW_SHOT = """
Transcript:
\"\"\"
Admin should be able to manage employees. Want to track attendance. GPS tagging needed. Employees should mark check-in and check-out. Export attendance to Excel. 
\"\"\"

Expected JSON (shortened):
{
  "epics": [
    {
      "id": "epic-1",
      "title": "Employee Management",
      "description": "Admin can manage employees, attendance, and GPS-tagging.",
      "stories": [
        {
          "id": "story-1",
          "title": "Create Employee Records",
          "description": "Admin can create employee profiles with basic info.",
          "acceptance_criteria": [
            "Admin can create new employee",
            "Employee is added to database",
            "Validation errors shown if fields missing"
          ],
          "priority": "high"
        },
        {
          "id": "story-2",
          "title": "GPS-based Check-in / Check-out",
          "description": "Employees can mark attendance with GPS tagging.",
          "acceptance_criteria": [
            "Check-in captures GPS",
            "Check-out captures GPS",
            "System validates geo-fence"
          ],
          "priority": "medium"
        },
        {
          "id": "story-3",
          "title": "Export Attendance",
          "description": "Admin can export daily/monthly attendance to Excel.",
          "acceptance_criteria": [
            "Export button is visible",
            "Exports all attendance fields",
            "Supports date range filtering"
          ],
          "priority": "medium"
        }
      ]
    }
  ]
}
Another Example:
Input Transcript:
\"\"\"
User wants ability to filter items by tag and export filtered list.
\"\"\"

Expected JSON (abridged):
{
  "epics": [
    {
      "id": "epic-1",
      "title": "List filtering and export",
      "stories": [
        {
          "id": "story-1",
          "title": "Add tag filtering",
          "description": "Allow users to filter list items by tag.",
          "acceptance_criteria": ["Filter dropdown visible", "Applying filter updates the list"],
          "priority": "medium"
        },
        {
          "id": "story-2",
          "title": "Export filtered list",
          "description": "Enable exporting the currently filtered list as CSV.",
          "acceptance_criteria": ["Export button visible", "Export respects filters"]
        }
      ]
    }
  ]
}
"""

# -----------------------
# REVIEWER PROMPT (main review template)
# -----------------------
REVIEWER_PROMPT = """
You are a Senior Agile Reviewer. 
Your ONLY task is to evaluate epics and stories and flag issues BRIEFLY.

YOU MUST return exactly this JSON structure:

{
  "review": {
    "epics": [
      {
        "id": "string",
        "clarity_ok": true/false,
        "missing_fields": [],
        "notes": "string"
      }
    ],
    "context": {}
  }
}

RULES:
- ONLY include epic-level review. DO NOT REVIEW STORIES.
- DO NOT include acceptance criteria issues.
- DO NOT include detailed QA checks.
- DO NOT include story-level rewrites.
- DO NOT include long text blocks.
- NEVER include fields like "checks", "suggested_changes", "rationale".
- NEVER include comments, markdown, or text outside JSON.
- Your ENTIRE OUTPUT must be ONE valid JSON object ONLY.
"""

# -----------------------
# REVIEWER FEW-SHOT (example)
# -----------------------
REVIEWER_FEW_SHOT = """
Example Input:
{
  "epics": [
    {"id":"E1","title":"User Login","description":"...","stories":[]}
  ]
}

Example Output:
{
  "review": {
    "epics": [
      {
        "id": "E1",
        "clarity_ok": true,
        "missing_fields": [],
        "notes": "Epic is clear and complete."
      }
    ],
    "context": {}
  }
}
"""

# -----------------------
# RUBRIC / REVIEW CHECKLIST (human-readable)
# -----------------------
REVIEW_RUBRIC = """
Reviewer Rubric (for model & evaluators):
- Clarity: story title describes a single user action/goal.
- Testability: acceptance criteria must be concrete (observable and measurable).
- Completeness: story has at least one AC and a short description.
- Size: story should be small enough for 1 sprint (<=8 points). If larger, flag as epic candidate.
- Dependencies: if story references external services or other modules, ensure dependencies are present.
"""

# -----------------------
# RECOMMENDED LLM SETTINGS (use with your LLM client)
# -----------------------
LLM_DEFAULTS = {
    "temperature": 0.0,
    "max_tokens": 2000,
    "top_p": 1.0,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0,
    "stop": None
}

# -----------------------
# HELPER NOTE (how to use)
# -----------------------
USAGE_NOTE = """
Usage:
1) Fill placeholders in PLANNER_PROMPT with the transcript and metadata.
2) Send messages in the format expected by your LLM (system + user/content).
3) Parse the returned JSON strictly (use a JSON schema validator).
4) Pass the planner JSON output to the REVIEWER_PROMPT (filling planner_json).
5) Use reviewer output to surface issues in the UI and to prompt the human-in-the-loop for corrections.
"""
