from docker import DockerClient, from_env
from docker.errors import DockerException
from http_target_discovery.enums.discovery_target_network_strategy import DiscoveryTargetNetworkStrategy
from http_target_discovery.providers.base_provider import BaseProvider
from http_target_discovery.schemas.target_schema import TargetSchema

class DockerProvider(BaseProvider):
    @classmethod
    def targets(cls) -> set[TargetSchema]:
        client: DockerClient | None = None
        targets: set[TargetSchema] = set()
        try:
            client = from_env()
            targets.update(cls._internal_targets(client))
            targets.update(cls._published_targets(client))
        except DockerException as e:
            raise RuntimeError("Failed to query Docker for targets") from e
        finally:
            if client is not None:
                client.close()
        if not targets:
            raise RuntimeError("No available targets")
        return targets

    @classmethod
    def _internal_targets(cls, client: DockerClient) -> set[TargetSchema]:
        from http_target_discovery.settings import settings

        if settings.target_network_strategy is DiscoveryTargetNetworkStrategy.PUBLISHED:
            return set()

        targets: set[TargetSchema] = set()
        for container in client.containers.list(filters={"label": settings.docker_target_label}):
            internal_ip: str | None = next(
                (
                    network.get("IPAddress")
                    for network in (container.attrs.get("NetworkSettings", {}).get("Networks") or {}).values()
                    if network.get("IPAddress")
                ),
                None
            )

            internal_port: str | None = next(iter(container.attrs.get("Config", {}).get("ExposedPorts") or {}), None)
            if internal_ip and internal_port:
                targets.add(
                    TargetSchema(
                        ip=internal_ip,
                        port=int(internal_port.split("/")[0])
                    )
                )

        return targets

    @classmethod
    def _published_targets(cls, client: DockerClient) -> set[TargetSchema]:
        from http_target_discovery.settings import settings

        if settings.target_network_strategy is DiscoveryTargetNetworkStrategy.INTERNAL:
            return set()

        targets: set[TargetSchema] = set()
        for container in client.containers.list(filters={"label": settings.docker_target_label}):
            for port_bindings in (container.attrs.get("NetworkSettings", {}).get("Ports") or {}).values():
                if not port_bindings:
                    continue

                port_binding = port_bindings[0]
                published_port = port_binding.get("HostPort")
                if not published_port:
                    continue

                published_ip: str = port_binding.get("HostIp") or "127.0.0.1"
                targets.add(
                    TargetSchema(
                        ip="127.0.0.1" if published_ip in {"0.0.0.0", "::"} else published_ip,
                        port=int(published_port)
                    )
                )

                break

        return targets
