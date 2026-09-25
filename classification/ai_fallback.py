"""
AI Fallback Classifier for Ambiguous Jobs
Invoked only when rule-based confidence is low (< 0.60) and an API key is available.
Never invoked for high-confidence jobs.
"""

import os
import json
from typing import Dict, Any, Optional
import requests


def classify_with_ai(
    title: str,
    department: str = "",
    skills: list = None,
    description: str = ""
) -> Optional[Dict[str, Any]]:
    """
    Fallback AI classifier for ambiguous roles.
    Returns structured JSON with domain, family, confidence, and reason.
    """
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
        
    prompt = f"""You are an expert IT job taxonomy classifier.
Analyze the following job details and classify into strict JSON:
Title: {title}
Department: {department}
Skills: {skills or []}
Description snippet: {description[:1500] if description else ''}

Return JSON with exact keys:
{{
  "is_it_job": true/false,
  "job_family": "<IT Job Family or null>",
  "primary_domain": "<Primary Domain or null>",
  "secondary_domains": ["<Secondary Domain 1>", ...],
  "specializations": ["<Specialization 1>", ...],
  "programming_languages": ["<Lang 1>", ...],
  "frameworks": ["<Framework 1>", ...],
  "confidence": 0.0 to 1.0,
  "reason": "<One sentence reason>"
}}
"""
    try:
        if os.getenv("OPENAI_API_KEY"):
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1
                },
                timeout=12
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)
    except Exception:
        return None
        
    return None
