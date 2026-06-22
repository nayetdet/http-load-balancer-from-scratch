from __future__ import annotations

import socket
import threading
import time
from loguru import logger
from http import HTTPStatus
from http_load_balancer.servers.base_server import BaseServer
from http_load_balancer.servers.handlers.http_handler import http_handler
from http_load_balancer.algorithms.base_algorithm import BaseAlgorithm
from http_load_balancer.core.target_manager import TargetManager
from http_load_balancer.core.target_stats_manager import TargetStatsManager
from http_load_balancer.schemas.connection_schema import ConnectionSchema
from http_load_balancer.schemas.target_schema import TargetSchema
from http_load_balancer.settings import settings
from http_load_balancer.utils.http_utils import HTTPUtils

_selection_lock = threading.Lock()

class ProxyServer(BaseServer):
    def __init__(
        self,
        host: str = settings.host,
        port: int = settings.proxy_port,
        backlog: int = settings.backlog,
        buffer_size: int = settings.buffer_size
    ) -> None:
        super().__init__(
            host=host,
            port=port,
            backlog=backlog,
            buffer_size=buffer_size
        )

    @http_handler()
    def handle_proxy_request(self, client_socket: socket.socket, request: bytes) -> None:
        with _selection_lock:
            targets: list[TargetSchema] = list(TargetManager.targets())
            if not targets:
                logger.warning("No targets available; returning 503")
                client_socket.sendall(HTTPUtils.response(HTTPStatus.SERVICE_UNAVAILABLE))
                return

            algorithm: type[BaseAlgorithm] = TargetManager.algorithm()
            connection: ConnectionSchema = ConnectionSchema.model_validate(dict(zip(ConnectionSchema.model_fields, client_socket.getpeername())))

            try:
                target: TargetSchema = algorithm.next_target(connection)
            except (ValueError, ZeroDivisionError):
                logger.warning("Target selection failed because no targets were available")
                client_socket.sendall(HTTPUtils.response(HTTPStatus.SERVICE_UNAVAILABLE))
                return

            TargetStatsManager.increment_connections(target.key())

        started_at: float = time.perf_counter()
        logger.info("Forwarding request to {}:{} via {}", target.ip, target.port, algorithm.__name__)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as remote_socket:
            try:
                remote_socket.connect((target.ip, target.port))
                remote_socket.sendall(request)
                while True:
                    response: bytes = remote_socket.recv(self._buffer_size)
                    if not response:
                        break
                    client_socket.sendall(response)
            except OSError:
                logger.exception("Failed to forward request to {}:{}", target.ip, target.port)
                try:
                    client_socket.sendall(HTTPUtils.response(HTTPStatus.BAD_GATEWAY))
                except OSError:
                    pass
            else:
                TargetStatsManager.update_response_time(target_key=target.key(), response_time=time.perf_counter() - started_at,)
            finally:
                TargetStatsManager.decrement_connections(target.key())
