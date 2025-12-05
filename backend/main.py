# backend/main.py
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from pydantic import BaseModel
from backend.agents.pipeline import RequirementsPipeline
import traceback
from backend.jira.jira_client import JiraClient

app = FastAPI(
    title="Agentic Requirements Assistant",
    version="1.0.0",
    description="Pipeline: Planner → Epic Generator → Reviewer → Unified Result"
)

# Request model
class TranscriptInput(BaseModel):
    transcript: str

pipeline = RequirementsPipeline()

class JiraSyncRequest(BaseModel):
    payload: dict   # approved payload from frontend

@app.get("/")
def root():
    return {"status": "ok", "message": "Agentic Requirements API running"}


@app.post("/api/process")
def process_transcript(input_data: TranscriptInput):
    """
    Accept transcript text and run the full Planner + Reviewer pipeline.
    """
    try:
        result = pipeline.run(input_data.transcript)
        return {"success": True, "result": result}
    except Exception as e:
        print("\n\n===== BACKEND EXCEPTION (PLAIN TEXT) =====")
        traceback.print_exc()
        print("===== END EXCEPTION =====\n\n")
        return {"success": False, "error": str(e)}

@app.post("/api/jira/sync")
def jira_sync(req: JiraSyncRequest):
    try:
        jira = JiraClient()
        # payload should be the approved payload (epics with approved stories)
        result = jira.sync_approved_payload(req.payload)
        return {"success": True, "result": result}
    except Exception as e:
        # return useful error
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}