"""
================================================================================
WUMPUS WORLD - LOGICAL AGENT
================================================================================

IMPLEMENTED INTELLIGENT MECHANISMS:
-----------------------------------
1. KNOWLEDGE BASE (Wissensdatenbank)
   - Tracks visited cells, safe cells, pit-safe cells, wumpus-safe cells
   - A cell is "safe" only if it's safe from BOTH pits AND wumpus

2. LOGICAL INFERENCE (Logische Schlussfolgerung)
   - No breeze -> all adjacent cells are pit-safe
   - No stench -> all adjacent cells are wumpus-safe

3. BFS PATHFINDING (Breitensuche)
   - Plans optimal routes through safe cells
   - Considers orientation (turning costs steps)

4. MANHATTAN DISTANCE HEURISTIC
   - Prioritizes exploring nearest safe cells first
   - Reduces unnecessary movement

5. SAFE EXPLORATION STRATEGY (Sichere Erkundung)
   - Explores fully safe cells
   - Returns home when no exploration possible

6. WUMPUS SHOOTING (Wumpus Bekaempfung)
   - When stuck, shoots at unvisited cell from stench location
   - On wumpus death: pit-safe cells become fully safe

================================================================================
"""

from wumpus import Orientation, Actions, Percepts


class Agent:
    """Logical Wumpus World Agent"""

    def __init__(self, size=(4, 4)):
        self.size = size
        self.width, self.height = size

    def new_episode(self):
        """Reset agent state for new episode."""
        self.pos = (0, 0)
        self.orientation = Orientation.EAST  # Explorer starts facing right/east
        self.has_gold = False
        self.has_arrow = True
        self.wumpus_alive = True

        # NOTE: Knowledge base
        self.visited = {(0, 0)}
        self.safe = {(0, 0)}
        self.pit_safe = {(0, 0)}
        self.wumpus_safe = {(0, 0)}
        self.stench_at = set()

        # NOTE: Planning
        self.plan = []

        # NOTE: Track if last action was a successful move (for bump handling)
        self.actually_moved = False

    def get_action(self, percept, reward):
        """Main decision function - returns next action based on percepts."""
        breeze = percept[Percepts.BREEZE]
        glitter = percept[Percepts.GLITTER]
        bump = percept[Percepts.BUMP]
        stench = percept[Percepts.STENCH]
        scream = percept[Percepts.SCREAM]

        # NOTE: Handle bump - correct position
        if bump:
            self.pos = self._get_previous_position()

        # NOTE: Handle wumpus death - pit-safe cells become fully safe
        if scream:
            self.wumpus_alive = False
            for cell in self.pit_safe:
                self.wumpus_safe.add(cell)
                self.safe.add(cell)

        # NOTE: Update knowledge base
        self.visited.add(self.pos)
        self.safe.add(self.pos)

        # NOTE: Track stench locations
        if stench:
            self.stench_at.add(self.pos)

        # NOTE: Grab gold immediately
        if glitter:
            self.has_gold = True
            return Actions.GRAB

        # NOTE: Update safe cells based on percepts
        self._update_knowledge(breeze, stench)

        # NOTE: If we have gold -> go home
        if self.has_gold:
            if self.pos == (0, 0):
                return Actions.CLIMB
            action = self._plan_route_to((0, 0))
            if action is not None:
                self._execute_action(action)
                return action

        # NOTE: Execute existing plan
        if self.plan:
            action = self.plan.pop(0)
            self._execute_action(action)
            return action

        # NOTE: Explore nearest safe unvisited cell (Manhattan distance)
        safe_unvisited = self.safe - self.visited
        if safe_unvisited:
            target = min(safe_unvisited, key=lambda c: self._manhattan(self.pos, c))
            action = self._plan_route_to(target)
            if action is not None:
                self._execute_action(action)
                return action

        # NOTE: If stuck and wumpus alive, try to shoot it
        if self.wumpus_alive and self.has_arrow and self.pos in self.stench_at:
            adjacent = self._get_adjacent(self.pos)
            for cell in adjacent:
                if cell not in self.visited:
                    return self._shoot_at_cell(cell)

        # NOTE: Go home if nothing else to do
        if self.pos != (0, 0):
            action = self._plan_route_to((0, 0))
            if action is not None:
                self._execute_action(action)
                return action

        return Actions.CLIMB

    # SECTION: =============== KNOWLEDGE UPDATE ====================

    def _update_knowledge(self, breeze, stench):
        """Update knowledge base based on current percepts."""
        adjacent = self._get_adjacent(self.pos)

        # NOTE: No breeze -> adjacent cells are pit-safe
        if not breeze:
            for cell in adjacent:
                self.pit_safe.add(cell)

        # NOTE: No stench -> adjacent cells are wumpus-safe
        if not stench:
            for cell in adjacent:
                self.wumpus_safe.add(cell)

        # NOTE: Cell is safe if BOTH pit-safe AND wumpus-safe
        for cell in adjacent:
            if cell in self.pit_safe and cell in self.wumpus_safe:
                self.safe.add(cell)

    # SECTION: =============== WUMPUS SHOOTING ====================

    def _shoot_at_cell(self, target):
        """Turn towards target cell and shoot."""
        dx = target[0] - self.pos[0]
        dy = target[1] - self.pos[1]

        if dx == 1:
            needed = Orientation.EAST
        elif dx == -1:
            needed = Orientation.WEST
        elif dy == -1:  # Fixed: target above = NORTH (y decreases)
            needed = Orientation.NORTH
        else:  # dy == 1, target below = SOUTH
            needed = Orientation.SOUTH

        # NOTE: Turn if not facing target
        if self.orientation != needed:
            # NOTE: Check if RIGHT gets us closer
            if self._turn(self.orientation, Actions.RIGHT) == needed:
                action = Actions.RIGHT
            else:
                action = Actions.LEFT
            self._execute_action(action)
            return action

        # NOTE: Shoot
        self.has_arrow = False
        return Actions.SHOOT

    # SECTION: =============== BFS PATHFINDING ====================

    def _plan_route_to(self, goal):
        """BFS pathfinding through safe cells."""
        if self.pos == goal:
            return None

        queue = [(self.pos, self.orientation, [])]
        visited = {(self.pos, self.orientation)}
        idx = 0

        while idx < len(queue):
            pos, orient, path = queue[idx]
            idx += 1

            if pos == goal:
                if path:
                    self.plan = path[1:]
                    return path[0]
                return None

            # NOTE: Try turning
            for turn in [Actions.LEFT, Actions.RIGHT]:
                new_orient = self._turn(orient, turn)
                state = (pos, new_orient)
                if state not in visited:
                    visited.add(state)
                    queue.append((pos, new_orient, path + [turn]))

            # NOTE: Try moving forward
            next_pos = self._get_forward_position(pos, orient)
            if next_pos and next_pos in self.safe:
                state = (next_pos, orient)
                if state not in visited:
                    visited.add(state)
                    queue.append((next_pos, orient, path + [Actions.FORWARD]))

        return None

    # SECTION: ============== HELPER FUNCTIONS ====================

    def _get_adjacent(self, pos):
        """Get valid adjacent cells."""
        x, y = pos
        adjacent = []
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                adjacent.append((nx, ny))
        return adjacent

    def _manhattan(self, pos1, pos2):
        """Manhattan distance between two positions."""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def _get_forward_position(self, pos, orient):
        """Calculate position after moving forward.

        NOTE: Y-axis matches environment (screen coordinates):
        - NORTH/up = y - 1
        - SOUTH/down = y + 1
        """
        x, y = pos
        if orient == Orientation.EAST:
            nx, ny = x + 1, y
        elif orient == Orientation.NORTH:
            nx, ny = x, y - 1  # Fixed: up = -y
        elif orient == Orientation.WEST:
            nx, ny = x - 1, y
        else:  # SOUTH
            nx, ny = x, y + 1  # Fixed: down = +y

        if 0 <= nx < self.width and 0 <= ny < self.height:
            return (nx, ny)
        return None

    def _get_previous_position(self):
        """Calculate previous position (after bump).

        NOTE: This is the opposite of forward movement.
        """
        x, y = self.pos
        if self.orientation == Orientation.EAST:
            return (x - 1, y)
        elif self.orientation == Orientation.NORTH:
            return (x, y + 1)  # Fixed: opposite of forward (-y)
        elif self.orientation == Orientation.WEST:
            return (x + 1, y)
        else:  # SOUTH
            return (x, y - 1)  # Fixed: opposite of forward (+y)

    def _turn(self, orient, action):
        """Calculate new orientation after turn."""
        if action == Actions.LEFT:
            return (orient - 1) % 4
        elif action == Actions.RIGHT:
            return (orient + 1) % 4
        return orient

    def _execute_action(self, action):
        """Update internal state after executing action."""
        if action == Actions.FORWARD:
            next_pos = self._get_forward_position(self.pos, self.orientation)
            if next_pos:
                self.pos = next_pos
        elif action == Actions.LEFT:
            self.orientation = self._turn(self.orientation, Actions.LEFT)
        elif action == Actions.RIGHT:
            self.orientation = self._turn(self.orientation, Actions.RIGHT)
        elif action == Actions.GRAB:
            self.has_gold = True
