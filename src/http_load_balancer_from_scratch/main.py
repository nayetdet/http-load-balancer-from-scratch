import socket
from loguru import logger

HOST = "127.0.0.1"
PORT = 8081

TARGET_HOST = "127.0.0.1"
TARGET_PORT = 8080
BUFFER_SIZE = 4096

def forward_request(client_socket):
    request = client_socket.recv(BUFFER_SIZE)
    if not request:
        client_socket.close()
        return

    logger.info(f"Repassando requisição para {TARGET_HOST}:{TARGET_PORT}")
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_socket.connect((TARGET_HOST, TARGET_PORT))
    remote_socket.sendall(request)

    while True:
        response = remote_socket.recv(BUFFER_SIZE)
        if not response:
            break
        client_socket.sendall(response)

    remote_socket.close()
    client_socket.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(10)

    logger.info(f"Proxy rodando em {HOST}:{PORT} -> {TARGET_HOST}:{TARGET_PORT}")
    while True:
        client_socket, _ = server.accept()
        forward_request(client_socket)
