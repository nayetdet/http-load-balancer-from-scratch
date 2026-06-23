from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException
from http_target_discovery.providers.base_provider import BaseProvider
from http_target_discovery.enums.network_strategy import NetworkStrategy
from http_target_discovery.schemas.target_schema import TargetSchema

def load_kubernetes() -> None:
    try:
        config.load_incluster_config()
    except ConfigException:
        config.load_kube_config()

class KubernetesProvider(BaseProvider):
    _apps: client.AppsV1Api = client.AppsV1Api()
    _core: client.CoreV1Api = client.CoreV1Api()

    @classmethod
    def targets(cls) -> set[TargetSchema]:
        from http_target_discovery.settings import settings

        deployment: client.V1Deployment = cls._apps.read_namespaced_deployment(
            name=settings.kubernetes_deployment_name,
            namespace=settings.kubernetes_namespace
        )

        replica_set_uids: set[str] = {
            replica_set.metadata.uid
            for replica_set in cls._apps.list_namespaced_replica_set(namespace=settings.kubernetes_namespace).items
            if any(
                owner.kind == "Deployment" and owner.uid == deployment.metadata.uid
                for owner in replica_set.metadata.owner_references or []
            )
        }

        pods: client.V1PodList = cls._core.list_namespaced_pod(namespace=settings.kubernetes_namespace)
        running_pods: list[client.V1Pod] = [
            pod
            for pod in pods.items
            if pod.status.phase == "Running"
            and any(
                owner.kind == "ReplicaSet" and owner.uid in replica_set_uids
                for owner in pod.metadata.owner_references or []
            )
            and any(
                condition.type == "Ready" and condition.status == "True"
                for condition in pod.status.conditions or []
            )
        ]

        targets: set[TargetSchema] = set()
        targets.update(cls._internal_targets(running_pods))
        targets.update(cls._published_targets(running_pods))
        return targets

    @classmethod
    def _internal_targets(cls, pods: list[client.V1Pod]) -> set[TargetSchema]:
        from http_target_discovery.settings import settings

        if settings.network_strategy is NetworkStrategy.PUBLISHED:
            return set()

        targets: set[TargetSchema] = set()
        for pod in pods:
            pod_ip: str | None = pod.status.pod_ip
            if not pod_ip:
                continue

            for container in pod.spec.containers or []:
                for port in container.ports or []:
                    container_port: int | None = getattr(port, "container_port", None)
                    if not container_port:
                        continue

                    targets.add(
                        TargetSchema(
                            ip=pod_ip,
                            port=int(container_port)
                        )
                    )

        return targets

    @classmethod
    def _published_targets(cls, pods: list[client.V1Pod]) -> set[TargetSchema]:
        from http_target_discovery.settings import settings

        if settings.network_strategy is NetworkStrategy.INTERNAL:
            return set()

        targets: set[TargetSchema] = set()
        for pod in pods:
            host_ip: str | None = pod.status.host_ip
            if not host_ip:
                continue

            host_network: bool = bool(getattr(pod.spec, "host_network", False))
            for container in pod.spec.containers or []:
                for port in container.ports or []:
                    host_port: int | None = getattr(port, "host_port", None)
                    container_port: int | None = getattr(port, "container_port", None)
                    if host_port:
                        targets.add(
                            TargetSchema(
                                ip=host_ip,
                                port=int(host_port)
                            )
                        )

                        continue

                    if not host_network or not container_port:
                        continue

                    targets.add(
                        TargetSchema(
                            ip=host_ip,
                            port=int(container_port)
                        )
                    )

        return targets
