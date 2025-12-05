# backend/llm/llm_client.py

import os
from mistralai import Mistral
import streamlit as st

class LLMClient:
    """
    Lightweight wrapper for Mistral AI chat models.
    """

    def __init__(self, model: str = "mistral-small-latest"):
        api_key = st.secrets["MISTRAL_API_KEY"]
        if not api_key:
            raise ValueError("MISTRAL_API_KEY not found. Please add it to your .env file.")

        self.client = Mistral(api_key=api_key)
        self.model = model

    def chat(self, system: str, user: str, temperature: float = 0.0, max_tokens: int = 2000):
        """
        Sends chat messages to Mistral and returns the text content.
        """
        response = self.client.chat.complete(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content
