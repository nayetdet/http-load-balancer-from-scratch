from enum import Enum

class AlgorithmStrategy(str, Enum):
    LEAST_CONNECTIONS = "least_connections"
    LEAST_RESPONSE_TIME = "least_response_time"
    IP_HASH = "ip_hash"
    ROUND_ROBIN = "round_robin"
    STICKY_ROUND_ROBIN = "sticky_round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
