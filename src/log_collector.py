import os
import sys
from kubernetes import client, config

def get_k8s_client():
    kubeconfig_path = os.environ.get("KUBECONFIG")
    if kubeconfig_path and os.path.exists(kubeconfig_path):
        config.load_kube_config(config_file=kubeconfig_path)
    else:
        try:
            config.load_incluster_config()
        except Exception:
            config.load_kube_config()
    return client.CoreV1Api(), client.AppsV1Api()

def collect_k8s_diagnostics(deployment_name: str, namespace: str) -> dict:
    v1, apps_v1 = get_k8s_client()
    diagnostics = {
        "deployment": deployment_name,
        "namespace": namespace,
        "events": [],
        "pod_statuses": [],
        "logs": []
    }

    try:
        dep = apps_v1.read_namespaced_deployment(deployment_name, namespace)
        labels = dep.spec.selector.match_labels
        selector = ",".join([f"{k}={v}" for k, v in labels.items()])
    except Exception as e:
        diagnostics["events"].append(f"Failed to fetch deployment '{deployment_name}': {str(e)}")
        return diagnostics

    # 1. Inspect Pods matching the deployment
    pods = v1.list_namespaced_pod(namespace, label_selector=selector)
    for pod in pods.items:
        p_name = pod.metadata.name
        statuses = pod.status.container_statuses or []
        for s in statuses:
            waiting_reason = s.state.waiting.reason if s.state.waiting else None
            waiting_message = s.state.waiting.message if s.state.waiting else None
            terminated_reason = s.state.terminated.reason if s.state.terminated else None

            diagnostics["pod_statuses"].append({
                "pod": p_name,
                "container": s.name,
                "ready": s.ready,
                "restarts": s.restart_count,
                "waiting_reason": waiting_reason,
                "waiting_message": waiting_message,
                "terminated_reason": terminated_reason
            })

        # Try to pull crash logs first (previous=True), fall back to live logs
        try:
            logs = v1.read_namespaced_pod_log(p_name, namespace, tail_lines=60, previous=True)
            diagnostics["logs"].append({"pod": p_name, "logs": logs})
        except Exception:
            try:
                logs = v1.read_namespaced_pod_log(p_name, namespace, tail_lines=60)
                diagnostics["logs"].append({"pod": p_name, "logs": logs})
            except Exception:
                diagnostics["logs"].append({"pod": p_name, "logs": "No log output available."})

    # 2. Collect Warning Events in the namespace
    events = v1.list_namespaced_event(namespace)
    for ev in events.items:
        if ev.type == "Warning":
            involved_name = ev.involved_object.name or ""
            diagnostics["events"].append(f"[{ev.reason}] {involved_name}: {ev.message}")

    return diagnostics