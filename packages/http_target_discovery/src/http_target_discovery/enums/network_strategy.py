from enum import Enum

class NetworkStrategy(str, Enum):
    PUBLISHED = "published"
    INTERNAL = "internal"
    BOTH = "both"
