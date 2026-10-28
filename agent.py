import os

import requests

from database import SafetyDatabase


class SafetyAgent:
    def __init__(self, model_name="llama3"):
        self.db = SafetyDatabase()
        self.model_name = model_name
        self.ollama_url = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")

    def analyze_safety_trends(self):
        """
        Retrieves recent incidents from SQLite and queries the local LLM 
        for root-cause analysis and safety recommendations.
        """
        rows = self.db.get_all_incidents()
        if not rows:
            return "No incident data available for AI analysis yet. Log some test violations first!"

        # Summarize the latest incident logs for the LLM prompt
        incident_summary = "\n".join([
            f"- Time: {row[0]} | Violation: {row[1]} | Zone: {row[2]} | Confidence: {row[3]}"
            for row in rows[:15]  # Analyze the latest 15 incidents
        ])

        prompt = (
            "You are an expert industrial safety AI agent. Analyze the following workplace safety violation logs "
            "and provide a concise root-cause analysis, identify high-risk patterns, and suggest actionable corrective actions "
            "for site supervisors:\n\n"
            f"{incident_summary}\n\n"
            "Provide your response in clear, structured sections: 1. Key Patterns, 2. Root Cause Analysis, 3. Recommended Actions."
        )

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.model_name, "prompt": prompt, "stream": False},
                timeout=120,
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("Ollama returned an invalid analysis response")
            result = payload.get("response")
            if not isinstance(result, str):
                raise ValueError("Ollama returned an invalid analysis response")
            return result
        except (requests.RequestException, ValueError, KeyError) as e:
            return (
                f"Failed to connect to local Ollama LLM: {e}. "
                "Make sure Ollama is running and the selected model is available "
                f"(for example, `ollama run {self.model_name}`)."
            )

if __name__ == "__main__":
    agent = SafetyAgent()
    print("Running Safety Agent Analysis...")
    print(agent.analyze_safety_trends())