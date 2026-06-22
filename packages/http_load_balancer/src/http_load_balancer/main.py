import os
import signal
from loguru import logger
from http_load_balancer.core.target_manager import TargetManager
from http_load_balancer.servers.internal_server import InternalServer
from http_load_balancer.servers.proxy_server import ProxyServer
from http_load_balancer.settings import settings

def main() -> None:
    logger.info("PID: {}", os.getpid())
    TargetManager.reload()
    signal.signal(signal.SIGHUP, TargetManager.reload)

    proxy_server = ProxyServer()
    internal_server = InternalServer()

    logger.info("Proxy running on {}:{} with {}", settings.host, settings.proxy_port, TargetManager.algorithm().__name__)
    logger.info("Internal server running on {}:{}", settings.host, settings.internal_port)

    internal_server.serve()
    proxy_server.serve().join()
