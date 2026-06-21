from __future__ import annotations

from enum import Enum
from http_load_balancer.algorithms.base_algorithm import BaseAlgorithm
from http_load_balancer.algorithms.dynamic.least_connections_algorithm import LeastConnectionsAlgorithm
from http_load_balancer.algorithms.dynamic.least_response_time_algorithm import LeastResponseTimeAlgorithm
from http_load_balancer.algorithms.static.ip_hash_algorithm import IPHashAlgorithm
from http_load_balancer.algorithms.static.round_robin_algorithm import RoundRobinAlgorithm
from http_load_balancer.algorithms.static.sticky_round_robin_algorithm import StickyRoundRobinAlgorithm
from http_load_balancer.algorithms.static.weighted_round_robin_algorithm import WeightedRoundRobinAlgorithm

class AlgorithmStrategy(str, Enum):
    LEAST_CONNECTIONS = ("least_connections", LeastConnectionsAlgorithm)
    LEAST_RESPONSE_TIME = ("least_response_time", LeastResponseTimeAlgorithm)
    IP_HASH = ("ip_hash", IPHashAlgorithm)
    ROUND_ROBIN = ("round_robin", RoundRobinAlgorithm)
    STICKY_ROUND_ROBIN = ("sticky_round_robin", StickyRoundRobinAlgorithm)
    WEIGHTED_ROUND_ROBIN = ("weighted_round_robin", WeightedRoundRobinAlgorithm)

    def __new__(cls, name: str, algorithm: type[BaseAlgorithm]):
        obj = str.__new__(cls, name)
        obj._value_ = name
        obj.algorithm = algorithm
        return obj

    def __init__(self, name: str, algorithm: type[BaseAlgorithm]):
        self.label = name
