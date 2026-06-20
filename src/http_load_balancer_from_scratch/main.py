import socket
import time
import threading
from loguru import logger
from http_load_balancer_from_scratch.algorithms.base_algorithm import BaseAlgorithm
from http_load_balancer_from_scratch.core.target_manager import TargetManager
from http_load_balancer_from_scratch.schemas.connection_schema import ConnectionSchema
from http_load_balancer_from_scratch.schemas.target_schema import TargetSchema
from http_load_balancer_from_scratch.settings import settings

HOST = "127.0.0.1"
PORT = 8080
BUFFER_SIZE = 4096

_selection_lock = threading.Lock()

def client_connection(client_socket: socket.socket) -> ConnectionSchema:
    client_ip, client_port = client_socket.getpeername()
    return ConnectionSchema(client_ip=client_ip, client_port=client_port)

def forward_request(client_socket: socket.socket, algorithm: type[BaseAlgorithm]) -> None:
    with client_socket:
        request = client_socket.recv(BUFFER_SIZE)
        if not request:
            return

        with _selection_lock:
            connection: ConnectionSchema = client_connection(client_socket)
            target: TargetSchema = algorithm.next_target(connection)
            target_key = target.key()
            TargetManager.increment_connections(target_key)

        started_at: float = time.perf_counter()
        logger.info("Repassando requisição para {}:{} via {}", target.ip, target.port, algorithm.__name__)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as remote_socket:
            try:
                remote_socket.connect((target.ip, target.port))
                remote_socket.sendall(request)
                while True:
                    response = remote_socket.recv(BUFFER_SIZE)
                    if not response:
                        break
                    client_socket.sendall(response)
            except OSError:
                logger.exception("Falha ao repassar a requisição para {}:{}", target.ip, target.port)
                try: client_socket.sendall(b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
                except OSError:
                    pass
            else:
                TargetManager.update_response_time(
                    target_key=target_key,
                    response_time=time.perf_counter() - started_at,
                )
            finally:
                TargetManager.decrement_connections(target_key)

def main() -> None:
    algorithm: type[BaseAlgorithm] = settings.ALGORITHM.algorithm

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(10)

    logger.info("Proxy rodando em {}:{} com {}", HOST, PORT, algorithm.__name__)
    while True:
        client_socket, _ = server.accept()
        threading.Thread(
            target=forward_request,
            args=(client_socket, algorithm),
            daemon=True,
        ).start()
