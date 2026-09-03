import os
import json
from groq import Groq

def get_active_model(client: Groq) -> str:
    # Preferred order of chat models
    preferred = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it"
    ]
    try:
        model_list = client.models.list()
        available_ids = [m.id for m in model_list.data]
        print(f"[AI-Agent] Models accessible to your key: {available_ids}")

        # Pick the first preferred model that exists in available_ids
        for pref in preferred:
            if pref in available_ids:
                return pref

        # If none of the preferred match, take the first available text/chat model
        if available_ids:
            return available_ids[0]
    except Exception as e:
        print(f"[AI-Agent] Warning: Could not list models ({e}). Defaulting to llama-3.1-8b-instant.")
    
    return "llama-3.1-8b-instant"

def analyze_k8s_failure(diagnostics: dict) -> dict:
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        return {
            "root_cause": "LLM_API_KEY environment variable is not set.",
            "recommended_fix": "Expose GroQ_Secret inside the Jenkins environment block.",
            "action_type": "NONE"
        }

    client = Groq(api_key=api_key)
    selected_model = get_active_model(client)
    print(f"[AI-Agent] Using Groq model: {selected_model}")

    prompt = f"""
You are an expert Kubernetes Site Reliability Engineer (SRE).
Analyze the following Kubernetes failure data collected during a failed deployment rollout.

Deployment: {diagnostics.get('deployment')}
Namespace: {diagnostics.get('namespace')}
Pod States: {json.dumps(diagnostics.get('pod_statuses'), indent=2)}
Warning Events: {json.dumps(diagnostics.get('events')[-10:], indent=2)}
Container Logs: {json.dumps(diagnostics.get('logs'), indent=2)}

Tasks:
1. Identify the exact root cause (e.g. CrashLoopBackOff, missing env, bad image tag, OOMKilled).
2. Detail the exact fix needed.
3. Decide if Jenkins should execute a rollback (`ROLLBACK`) or take no automated action (`NONE`).

You MUST respond strictly in valid JSON format with this structure:
{{
  "root_cause": "Concise 1-3 sentences stating why the container failed",
  "recommended_fix": "Exact instructions or YAML adjustments to fix it",
  "action_type": "ROLLBACK" | "NONE"
}}
"""

    response = client.chat.completions.create(
        model=selected_model,
        messages=[
            {"role": "system", "content": "You are a Kubernetes troubleshooting assistant that outputs strictly valid JSON."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.1
    )

    try:
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {
            "root_cause": response.choices[0].message.content,
            "recommended_fix": "Review the logs and recommendations provided.",
            "action_type": "NONE"
        }