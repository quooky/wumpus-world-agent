"""
Wumpus World Enums and Constants
================================
This module provides the enums used by the logical agent.
"""

from enum import IntEnum


class Orientation(IntEnum):
    """Agent orientation in the grid."""
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3


class Actions(IntEnum):
    """Available agent actions."""
    FORWARD = 0
    LEFT = 1
    RIGHT = 2
    GRAB = 3
    SHOOT = 4
    CLIMB = 5


class Percepts(IntEnum):
    """Percept indices for the agent."""
    BREEZE = 0
    GLITTER = 1
    BUMP = 2
    STENCH = 3
    SCREAM = 4
