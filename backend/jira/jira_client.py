# backend/jira/jira_client.py

import os
import requests
from typing import Dict, Any, List

JIRA_SITE = os.getenv("JIRA_SITE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")
JIRA_PROJECT_ID = os.getenv("JIRA_PROJECT_ID")

if not (JIRA_SITE and JIRA_EMAIL and JIRA_API_TOKEN and JIRA_PROJECT_KEY):
    # we'll not raise here; caller should handle missing config
    pass

AUTH = (JIRA_EMAIL, JIRA_API_TOKEN)
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}


class JiraClient:
    def __init__(self):
        if not (JIRA_SITE and JIRA_EMAIL and JIRA_API_TOKEN and JIRA_PROJECT_KEY):
            raise ValueError("JIRA credentials missing. Please set JIRA_SITE_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY in .env")
        self.base = JIRA_SITE.rstrip("/")
        self.auth = AUTH

        # cache discovered field ids
        self.epic_name_field = None
        self.epic_link_field = None
        # call discovery now
        try:
            self.discover_fields()
        except Exception:
            # don't crash on init; allow caller to attempt discovery later
            pass

    def discover_fields(self):
        """Discover custom field ids for 'Epic Name' and 'Epic Link' in this Jira instance."""
        url = f"{self.base}/rest/api/3/field"
        r = requests.get(url, auth=self.auth, headers=HEADERS, timeout=30)
        try:
            r.raise_for_status()
        except Exception as e:
            print("\n❌ JIRA ERROR DETAILS:")
            print("Status:", r.status_code)
            try:
                print(r.json())
            except:
                print("Raw response:", r.text)
            raise e
        fields = r.json()
        for f in fields:
            name = f.get("name", "").lower()
            # common names
            if "epic name" == name:
                self.epic_name_field = f["id"]
            if "epic link" == name:
                self.epic_link_field = f["id"]

        # try some common fallbacks if not found
        # Many Jira Cloud instances use customfield_10014 for Epic Name and customfield_10008 for Epic Link
        if not self.epic_name_field:
            # check for id presence of 10014
            for f in fields:
                if f.get("id") == "customfield_10014":
                    self.epic_name_field = "customfield_10014"
                    break
        if not self.epic_link_field:
            for f in fields:
                if f.get("id") == "customfield_10008":
                    self.epic_link_field = "customfield_10008"
                    break

        return {"epic_name_field": self.epic_name_field, "epic_link_field": self.epic_link_field}

    def create_issue(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Jira issue and return the JSON response."""
        url = f"{self.base}/rest/api/3/issue"
        payload = {"fields": fields}
        r = requests.post(url, auth=self.auth, headers=HEADERS, json=payload, timeout=30)
        try:
            r.raise_for_status()
        except Exception as e:
            print("\n❌ JIRA ERROR DETAILS:")
            print("Status:", r.status_code)
            try:
                print(r.json())
            except:
                print("Raw response:", r.text)
            raise e
        return r.json()

    def _to_adf(self, text: str):
        """
        Converts plain text to Atlassian Document Format (ADF).
        """
        if not text:
            text = ""
        return {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": text}
                    ]
                }
            ]
        }

    def create_epic(self, epic: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates an Epic in a Team-Managed project.
        """
        fields = {
            "project": {"id": JIRA_PROJECT_ID},
            "summary": epic.get("title") or epic.get("id"),
            "description": self._to_adf(epic.get("description")),
            "issuetype": {"name": "Epic"},
        }

        if epic.get("labels"):
            fields["labels"] = epic.get("labels")

        return self.create_issue(fields)

    def create_story(self, story: Dict[str, Any], epic_jira_key: str) -> Dict[str, Any]:
        """
        Creates a story and links it to a Team-Managed Epic using parent field.
        """
        fields = {
            "project": {"id": JIRA_PROJECT_ID},
            "summary": story.get("title") or story.get("id"),
            "description": self._to_adf(self._build_story_description(story)),
            "issuetype": {"name": "Story"},
            "parent": {"key": epic_jira_key}  # <---- IMPORTANT FOR TMP
        }

        # labels
        if story.get("labels"):
            fields["labels"] = story.get("labels")

        created = self.create_issue(fields)
        return created


    def _build_story_description(self, story: Dict[str, Any]) -> str:
        """Compose a description embedding acceptance criteria as bullet list."""
        desc = story.get("description", "") or ""
        ac = story.get("acceptance_criteria", [])
        if ac:
            desc += "\n\nAcceptance Criteria:\n"
            for a in ac:
                desc += f"- {a}\n"
        # optionally append dependencies
        deps = story.get("dependencies", [])
        if deps:
            desc += "\nDependencies:\n"
            for d in deps:
                desc += f"- {d}\n"
        return desc

    def sync_approved_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        payload: {
           "epics": [ {id,title,description,priority,labels,stories:[{...}]} ],
           "context": {...}
        }
        Create epics first, then create stories under them. Returns mapping.
        """
        result = {"epics": []}
        for epic in payload.get("epics", []):
            created_epic = self.create_epic(epic)
            epic_key = created_epic.get("key")  # like REQR-123
            epic_result = {"requested_epic_id": epic.get("id"), "jira_key": epic_key, "stories": []}

            # create stories that were approved (epic already includes only approved stories)
            for s in epic.get("stories", []):
                created_story = self.create_story(s, epic_key)
                epic_result["stories"].append({
                    "requested_story_id": s.get("id"),
                    "jira_key": created_story.get("key")
                })

            result["epics"].append(epic_result)
        return result
