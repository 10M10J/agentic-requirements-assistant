# frontend/api_client.py

import requests

API_BASE = "http://127.0.0.1:8000"

def process_transcript(transcript: str):
    """
    Sends transcript text to the backend /api/process endpoint.
    Returns the parsed JSON.
    """
    url = f"{API_BASE}/api/process"

    response = requests.post(url, json={"transcript": transcript})

    if response.status_code != 200:
        raise Exception(f"Backend returned status {response.status_code}")

    data = response.json()

    if not data.get("success"):
        raise Exception(f"Backend error: {data.get('error')}")

    return data["result"]
