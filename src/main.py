import argparse
from log_collector import collect_k8s_diagnostics
from rca_agent import analyze_k8s_failure
from remediation import apply_remediation

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--deployment", required=True, help="Deployment name")
    parser.add_argument("--namespace", default="default", help="Kubernetes namespace")
    parser.add_argument("--auto-fix", default="true", help="Automatically trigger rollback/remediation")
    args = parser.parse_args()

    print(f"\n==================================================")
    print(f"  AI ROOT CAUSE INVESTIGATION: {args.deployment}")
    print(f"==================================================")

    # 1. Collect
    print("[1/3] Fetching Kubernetes Pod statuses, events, and logs...")
    diag = collect_k8s_diagnostics(args.deployment, args.namespace)

    # 2. Analyze
    print("[2/3] Querying Groq LLM for root cause analysis...")
    analysis = analyze_k8s_failure(diag)

    print("\n------------------- ANALYSIS ---------------------")
    print(f"ROOT CAUSE:\n{analysis.get('root_cause')}\n")
    print(f"RECOMMENDED FIX:\n{analysis.get('recommended_fix')}")
    print("--------------------------------------------------\n")

    # 3. Remediate
    if args.auto_fix.lower() == "true":
        print("[3/3] Evaluating remediation action...")
        apply_remediation(args.deployment, args.namespace, analysis.get("action_type", "NONE"))

if __name__ == "__main__":
    main()