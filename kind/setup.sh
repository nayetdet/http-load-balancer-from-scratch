#!/usr/bin/env bash
set -euo pipefail

SCRIPTS_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIND_CLUSTER_NAME="${KIND_CLUSTER_NAME:-kind}"
KIND_CONFIG="${KIND_CONFIG:-${SCRIPTS_PATH}/config.yaml}"

if kind get clusters | grep -qx "${KIND_CLUSTER_NAME}"; then
  echo "[kind] cluster ${KIND_CLUSTER_NAME} already exists, skipping creation"
else
  echo "[kind] creating cluster ${KIND_CLUSTER_NAME} from ${KIND_CONFIG}"
  kind create cluster --name "${KIND_CLUSTER_NAME}" --config "${KIND_CONFIG}"
fi

kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl -n kube-system patch deployment metrics-server --type='json' -p='[
  {"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"},
  {"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname"}
]' || true

kubectl -n kube-system rollout status deployment/metrics-server --timeout=180s
kubectl get apiservice v1beta1.metrics.k8s.io -o wide
kubectl top nodes
