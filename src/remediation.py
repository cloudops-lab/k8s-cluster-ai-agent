import os
import subprocess

def apply_remediation(deployment: str, namespace: str, action_type: str):
    kubeconfig = os.environ.get("KUBECONFIG")
    cmd_base = ["kubectl"]
    if kubeconfig:
        cmd_base.extend(["--kubeconfig", kubeconfig])

    if action_type == "ROLLBACK":
        print(f"\n[Remediation] Performing automatic rollback for deployment/{deployment} in namespace '{namespace}'...")
        cmd = cmd_base + ["rollout", "undo", f"deployment/{deployment}", "-n", namespace]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"[Remediation SUCCESS] {res.stdout.strip()}")
        else:
            print(f"[Remediation ERROR] Rollback failed: {res.stderr.strip()}")
    else:
        print("[Remediation] No automated action taken. Manual fix required based on RCA.")