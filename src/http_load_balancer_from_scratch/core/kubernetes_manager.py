from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException
from http_load_balancer_from_scratch.schemas.target_schema import TargetSchema
from http_load_balancer_from_scratch.settings import settings

try:
    config.load_incluster_config()
except ConfigException:
    config.load_kube_config()

class KubernetesManager:
    _core = client.CoreV1Api()

    @classmethod
    def targets(cls) -> list[TargetSchema]:
        pods = cls._core.list_namespaced_pod(
            namespace=settings.KUBERNETES_NAMESPACE,
            label_selector=f"app={settings.KUBERNETES_DEPLOYMENT_APP_NAME}"
        )

        targets: list[TargetSchema] = []
        for pod in pods.items:
            if pod.status.phase != "Running":
                continue

            ip: str = pod.status.pod_ip
            if not ip:
                continue

            port: int = pod.spec.containers[0].ports[0].container_port
            targets.append(TargetSchema(ip=ip, port=port))
        
        if not targets:
            raise RuntimeError("No available targets")
        return targets
