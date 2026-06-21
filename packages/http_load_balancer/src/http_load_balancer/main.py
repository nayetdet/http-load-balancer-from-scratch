import socket
import threading
import signal
import time
from loguru import logger
from http_load_balancer.core.target_stats_manager import TargetStatsManager
from http_load_balancer.core.target_manager import TargetManager
from http_load_balancer.schemas.connection_schema import ConnectionSchema
from http_load_balancer.schemas.target_schema import TargetSchema
from http_load_balancer.settings import settings

_selection_lock = threading.Lock()

def client_connection(client_socket: socket.socket) -> ConnectionSchema:
    client_ip, client_port = client_socket.getpeername()
    return ConnectionSchema(client_ip=client_ip, client_port=client_port)

def forward_request(client_socket: socket.socket, algorithm) -> None:
    with client_socket:
        request = client_socket.recv(settings.buffer_size)
        if not request:
            return

        with _selection_lock:
            connection: ConnectionSchema = client_connection(client_socket)
            target: TargetSchema = algorithm.next_target(connection)
            target_key = target.key()
            TargetStatsManager.increment_connections(target_key)

        started_at: float = time.perf_counter()
        logger.info("Forwarding request to {}:{} via {}", target.ip, target.port, algorithm.__name__)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as remote_socket:
            try:
                remote_socket.connect((target.ip, target.port))
                remote_socket.sendall(request)
                while True:
                    response = remote_socket.recv(settings.buffer_size)
                    if not response:
                        break
                    client_socket.sendall(response)
            except OSError:
                logger.exception("Failed to forward request to {}:{}", target.ip, target.port)
                try: client_socket.sendall(b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
                except OSError:
                    pass
            else:
                TargetStatsManager.update_response_time(
                    target_key=target_key,
                    response_time=time.perf_counter() - started_at,
                )
            finally:
                TargetStatsManager.decrement_connections(target_key)

def main() -> None:
    TargetManager.reload()
    signal.signal(signal.SIGHUP, TargetManager.reload)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((settings.host, settings.port))
    server.listen(settings.backlog)

    logger.info("Proxy running on {}:{} with {}", settings.host, settings.port, TargetManager.algorithm().__name__)
    while True:
        client_socket, _ = server.accept()
        threading.Thread(
            target=forward_request,
            args=(client_socket, TargetManager.algorithm()),
            daemon=True,
        ).start()
