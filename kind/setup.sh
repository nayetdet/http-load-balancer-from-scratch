#!/usr/bin/env bash
set -euo pipefail

scripts_path="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cluster_name="${KIND_CLUSTER_NAME:-kind}"
config="${KIND_CONFIG:-${scripts_path}/config.yaml}"

echo "Using cluster ${cluster_name}"
echo "Using config ${config}"
if kind get clusters | grep -qx "${cluster_name}"; then
  echo "Cluster ${cluster_name} already exists, reusing it"
else
  echo "Creating cluster ${cluster_name} from ${config}"
  kind create cluster --name "${cluster_name}" --config "${config}"
fi

echo "Exporting kubeconfig for ${cluster_name}"
kind export kubeconfig --name "${cluster_name}"

echo "Waiting for Kubernetes nodes to become Ready"
kubectl wait --for=condition=Ready nodes --all --timeout=120s

echo "Installing metrics-server"
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

echo "Patching metrics-server for kind compatibility"
kubectl -n kube-system patch deployment metrics-server --type='json' -p='[
  {"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"},
  {"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname"}
]'

echo "Waiting for metrics-server rollout"
kubectl -n kube-system rollout status deployment/metrics-server --timeout=180s

echo "Confirming metrics-server API is available"
kubectl get apiservice v1beta1.metrics.k8s.io -o wide
echo "Kubernetes development environment is ready"
