import os
import json
from groq import Groq

def analyze_k8s_failure(diagnostics: dict) -> dict:
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        return {
            "root_cause": "LLM_API_KEY environment variable is not set.",
            "recommended_fix": "Expose GroQ_Secret inside the Jenkins environment block.",
            "action_type": "NONE"
        }

    client = Groq(api_key=api_key)

    prompt = f"""
You are an expert Kubernetes Site Reliability Engineer (SRE).
Analyze the following Kubernetes failure data collected during a failed deployment rollout.

Deployment: {diagnostics.get('deployment')}
Namespace: {diagnostics.get('namespace')}
Pod States: {json.dumps(diagnostics.get('pod_statuses'), indent=2)}
Warning Events: {json.dumps(diagnostics.get('events')[-10:], indent=2)}
Container Logs: {json.dumps(diagnostics.get('logs'), indent=2)}

Tasks:
1. Identify the exact root cause (e.g. CrashLoopBackOff due to bad connection string, ImagePullBackOff, wrong port, OOMKilled, missing Secret/ConfigMap).
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
        model="llama-3.3-70b-versatile",
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
            "recommended_fix": "See raw output above.",
            "action_type": "NONE"
        }