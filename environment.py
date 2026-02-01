"""
Simple Wumpus World Environment
===============================
A clean environment that works directly with the logical agent.

Coordinate system (screen coordinates):
- (0,0) is top-left
- x increases to the right (EAST)
- y increases downward (SOUTH)
- Agent starts at (0,0) facing EAST
"""

import random
from wumpus import Orientation, Actions, Percepts


class WumpusWorld:
    """Simple 4x4 Wumpus World environment."""

    def __init__(self, size=(4,4), pit_probability=0.1, seed=None):
        """
        Initialize the Wumpus World.

        Args:
            size: Grid size (default 4x4)
            pit_probability: Chance of pit in each cell (default 0.2)
            seed: Random seed for reproducibility (optional)
        """
        self.size = size
        self.pit_probability = pit_probability

        if seed is not None:
            random.seed(seed)

        self.reset()

    def reset(self):
        """Reset the world for a new episode."""
        # Agent state
        self.agent_pos = (0, 0)
        self.agent_dir = Orientation.EAST
        self.agent_alive = True
        self.has_gold = False
        self.has_arrow = True
        self.exited = False

        # World state
        self.wumpus_alive = True
        self.wumpus_pos = None
        self.gold_pos = None
        self.pits = set()

        # Performance
        self.score = 0
        self.steps = 0

        # Last percept info
        self.bump = False
        self.scream = False

        # Generate world
        self._generate_world()

        return self.get_percept()

    def _generate_world(self):
        """Randomly generate pits, wumpus, and gold."""
        cells = [(x, y) for x in range(self.size[0]) for y in range(self.size[1])]
        cells.remove((0, 0))  # Start position is always safe

        # Place pits
        for cell in cells:
            if random.random() < self.pit_probability:
                self.pits.add(cell)

        # Place wumpus (not at start, not in pit)
        available = [c for c in cells if c not in self.pits]
        if available:
            self.wumpus_pos = random.choice(available)

        # Place gold (not at start)
        if available:
            self.gold_pos = random.choice(cells)

    def get_percept(self):
        """
        Get current percepts for the agent.

        Returns:
            dict: Percepts indexed by Percepts enum
        """
        x, y = self.agent_pos

        # Check adjacent cells for breeze (near pit) and stench (near wumpus)
        adjacent = self._get_adjacent(self.agent_pos)

        breeze = any(cell in self.pits for cell in adjacent)
        stench = self.wumpus_alive and self.wumpus_pos in adjacent
        glitter = self.agent_pos == self.gold_pos and not self.has_gold

        percept = {
            Percepts.BREEZE: breeze,
            Percepts.STENCH: stench,
            Percepts.GLITTER: glitter,
            Percepts.BUMP: self.bump,
            Percepts.SCREAM: self.scream,
        }

        # Reset one-time percepts
        self.bump = False
        self.scream = False

        return percept

    def step(self, action):
        """
        Execute an action and return the result.

        Args:
            action: Action from Actions enum

        Returns:
            tuple: (percept, reward, done, info)
        """
        if not self.agent_alive or self.exited:
            return self.get_percept(), 0, True, {'reason': 'game_over'}

        self.steps += 1
        reward = -1  # Each action costs 1 point
        info = {'action': action}

        if action == Actions.FORWARD:
            self._move_forward()
        elif action == Actions.LEFT:
            self._turn_left()
        elif action == Actions.RIGHT:
            self._turn_right()
        elif action == Actions.GRAB:
            self._grab()
        elif action == Actions.SHOOT:
            reward = -10  # Shooting costs 10 points
            self._shoot()
        elif action == Actions.CLIMB:
            self._climb()

        # Check for death
        if self.agent_pos in self.pits:
            self.agent_alive = False
            reward -= 1000
            info['reason'] = 'fell_in_pit'
        elif self.agent_pos == self.wumpus_pos and self.wumpus_alive:
            self.agent_alive = False
            reward -= 1000
            info['reason'] = 'eaten_by_wumpus'

        # Check for win
        if self.exited and self.has_gold:
            reward += 1000
            info['reason'] = 'escaped_with_gold'
        elif self.exited:
            info['reason'] = 'escaped_without_gold'

        self.score += reward
        done = not self.agent_alive or self.exited

        return self.get_percept(), reward, done, info

    def _move_forward(self):
        """Move agent forward in current direction."""
        x, y = self.agent_pos

        if self.agent_dir == Orientation.NORTH:
            new_pos = (x, y - 1)
        elif self.agent_dir == Orientation.SOUTH:
            new_pos = (x, y + 1)
        elif self.agent_dir == Orientation.EAST:
            new_pos = (x + 1, y)
        else:  # WEST
            new_pos = (x - 1, y)

        # Check bounds
        nx, ny = new_pos
        if 0 <= nx < self.size[0] and 0 <= ny < self.size[1]:
            self.agent_pos = new_pos
        else:
            self.bump = True

    def _turn_left(self):
        """Turn agent 90 degrees left."""
        self.agent_dir = Orientation((self.agent_dir - 1) % 4)

    def _turn_right(self):
        """Turn agent 90 degrees right."""
        self.agent_dir = Orientation((self.agent_dir + 1) % 4)

    def _grab(self):
        """Try to grab gold."""
        if self.agent_pos == self.gold_pos and not self.has_gold:
            self.has_gold = True
            self.gold_pos = None  # Gold picked up

    def _shoot(self):
        """Shoot arrow in current direction."""
        if not self.has_arrow:
            return

        self.has_arrow = False

        # Arrow travels in straight line
        x, y = self.agent_pos
        dx, dy = 0, 0

        if self.agent_dir == Orientation.NORTH:
            dy = -1
        elif self.agent_dir == Orientation.SOUTH:
            dy = 1
        elif self.agent_dir == Orientation.EAST:
            dx = 1
        else:  # WEST
            dx = -1

        # Check each cell in arrow path
        ax, ay = x + dx, y + dy
        while 0 <= ax < self.size[0] and 0 <= ay < self.size[1]:
            if (ax, ay) == self.wumpus_pos and self.wumpus_alive:
                self.wumpus_alive = False
                self.scream = True
                break
            ax, ay = ax + dx, ay + dy

    def _climb(self):
        """Try to climb out (only works at start position)."""
        if self.agent_pos == (0, 0):
            self.exited = True

    def _get_adjacent(self, pos):
        """Get valid adjacent cells."""
        x, y = pos
        adjacent = []
        for dx, dy in [(0, -1), (0, 1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size[0] and 0 <= ny < self.size[1]:
                adjacent.append((nx, ny))
        return adjacent


    def get_state(self):
        """Get full world state (for visualization)."""
        return {
            'agent_pos': self.agent_pos,
            'agent_dir': self.agent_dir,
            'agent_alive': self.agent_alive,
            'has_gold': self.has_gold,
            'has_arrow': self.has_arrow,
            'wumpus_pos': self.wumpus_pos,
            'wumpus_alive': self.wumpus_alive,
            'gold_pos': self.gold_pos,
            'pits': self.pits.copy(),
            'score': self.score,
            'steps': self.steps,
            'exited': self.exited,
            'size' : self.size,
        }


def run_episode(agent, size=(4,4), world=None, verbose=False, max_steps=100):
    """
    Run a single episode with an agent.

    Args:
        agent: Agent instance with new_episode() and get_action() methods
        world: WumpusWorld instance (created if None)
        verbose: Print each step
        max_steps: Maximum steps before timeout

    Returns:
        dict: Episode results
    """
    if world is None:
        world = WumpusWorld(size)

    agent.new_episode()
    percept = world.reset()

    if verbose:
        print("=== Starting Episode ===")
        world.render()

    done = False
    total_reward = 0

    for step in range(max_steps):
        action = agent.get_action(percept, reward=0)
        percept, reward, done, info = world.step(action)
        total_reward += reward

        if verbose:
            print(f"Action: {Actions(action).name}")
            world.render()

        if done:
            break

    result = {
        'score': world.score,
        'steps': world.steps,
        'alive': world.agent_alive,
        'has_gold': world.has_gold,
        'exited': world.exited,
        'won': world.exited and world.has_gold,
    }

    if verbose:
        print("=== Episode Complete ===")
        if result['won']:
            print("VICTORY! Escaped with gold!")
        elif result['exited']:
            print("Escaped without gold.")
        elif not result['alive']:
            print(f"DEATH: {info.get('reason', 'unknown')}")
        else:
            print("Timeout.")
        print(f"Final Score: {result['score']}")

    return result


def run_experiments(agent_class, size=(4,4), n_episodes=100, verbose=False):
    """
    Run multiple episodes and collect statistics.

    Args:
        agent_class: Agent class to instantiate
        n_episodes: Number of episodes to run
        verbose: Print progress

    Returns:
        dict: Aggregated statistics
    """
    results = []

    for i in range(n_episodes):
        agent = agent_class()
        result = run_episode(agent, size, verbose=False)
        results.append(result)

        if verbose and (i + 1) % 10 == 0:
            print(f"Completed {i + 1}/{n_episodes} episodes...")

    # Aggregate statistics
    wins = sum(1 for r in results if r['won'])
    deaths = sum(1 for r in results if not r['alive'])
    escapes = sum(1 for r in results if r['exited'] and not r['has_gold'])
    avg_score = sum(r['score'] for r in results) / n_episodes
    avg_steps = sum(r['steps'] for r in results) / n_episodes

    stats = {
        'n_episodes': n_episodes,
        'wins': wins,
        'win_rate': wins / n_episodes,
        'deaths': deaths,
        'death_rate': deaths / n_episodes,
        'escapes': escapes,
        'avg_score': avg_score,
        'avg_steps': avg_steps,
    }

    return stats


# Main entry point
if __name__ == '__main__':
    from solution import Agent

    print("=== Single Episode (Verbose) ===")
    agent = Agent()
    result = run_episode(agent, verbose=True)

    print("\n=== Running 100 Episodes ===")
    stats = run_experiments(Agent,size =(5,5), n_episodes=100, verbose=True)

    print("\n=== Results ===")
    print(f"Episodes: {stats['n_episodes']}")
    print(f"Wins: {stats['wins']} ({stats['win_rate']*100:.1f}%)")
    print(f"Deaths: {stats['deaths']} ({stats['death_rate']*100:.1f}%)")
    print(f"Escapes (no gold): {stats['escapes']}")
    print(f"Average Score: {stats['avg_score']:.1f}")
    print(f"Average Steps: {stats['avg_steps']:.1f}")
