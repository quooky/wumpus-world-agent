import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io
import imageio
import numpy as np
from IPython.display import clear_output, display
import time

# Better plot settings
plt.rcParams['figure.figsize'] = [14, 5]
plt.rcParams['figure.dpi'] = 100
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.titleweight'] = 'bold'
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'
plt.rcParams['axes.edgecolor'] = 'black'
plt.rcParams['axes.linewidth'] = 1.5

# Import our modules
from solution import Agent
from environment import WumpusWorld
from wumpus import Actions, Percepts, Orientation

class WumpusVisualizer:
    """Visualizes the Wumpus World and agent's knowledge base.
    
    Coordinate system: (0,0) at top-left, y increases downward.
    """
    
    def __init__(self, world, agent):
        self.world = world
        self.agent = agent
        self.path_history = [(0, 0)]
        self.step_count = 0

    def _base_grid(self,ax):
        state = self.world.get_state()
        width, height = state['size']
        ax.clear()
        
        ax.set_xlim(-0.5, width - 0.5)
        ax.set_ylim(-0.5, height - 0.5)
        ax.set_aspect('equal')
    
        # Draw grid lines
        for i in range(height + 1):
            ax.axhline(y=i - 0.5, color='black', linewidth=1)
        for j in range(width + 1):
            ax.axvline(x=j - 0.5, color='black', linewidth=1)
    
    def plot_world(self, ax):
        """Plot the actual world state."""
        self._base_grid(ax)
        state = self.world.get_state()
        
        # Draw pits
        for px, py in state['pits']:
            ax.add_patch(plt.Rectangle((px-0.5, py-0.5), 1, 1, 
                                        facecolor='black', alpha=0.7))
            ax.text(px, py, 'PIT', ha='center', va='center', fontsize=9, 
                   color='white', fontweight='bold')
        
        # Draw wumpus
        if state['wumpus_pos']:
            wx, wy = state['wumpus_pos']
            color = 'red' if state['wumpus_alive'] else 'gray'
            ax.add_patch(plt.Rectangle((wx-0.5, wy-0.5), 1, 1, 
                                        facecolor=color, alpha=0.5))
            label = 'W' if state['wumpus_alive'] else 'X'
            ax.text(wx, wy, label, ha='center', va='center', fontsize=14, 
                   fontweight='bold', color='darkred')
        
        # Draw gold
        if state['gold_pos']:
            gx, gy = state['gold_pos']
            ax.add_patch(plt.Rectangle((gx-0.5, gy-0.5), 1, 1, 
                                        facecolor='gold', alpha=0.5))
            ax.text(gx, gy, 'G', ha='center', va='center', fontsize=14, 
                   fontweight='bold', color='darkgoldenrod')
        
        # Draw start position (0,0)
        ax.add_patch(plt.Rectangle((-0.5, -0.5), 1, 1, 
                                    facecolor='lightgreen', alpha=0.3))
        ax.text(0, 0.35, 'START', ha='center', va='center', fontsize=7)
        
        # Draw agent path
        if len(self.path_history) > 1:
            path_x = [p[0] for p in self.path_history]
            path_y = [p[1] for p in self.path_history]
            ax.plot(path_x, path_y, 'b-', linewidth=2, alpha=0.5)
            ax.plot(path_x, path_y, 'bo', markersize=4)
        
        # Draw agent
        if state['agent_alive'] and not state['exited']:
            ax_pos, ay_pos = state['agent_pos']

            # Direction arrow
            dir_map = {
                Orientation.EAST: (0.3, 0),
                Orientation.WEST: (-0.3, 0),
                Orientation.NORTH: (0, -0.3),
                Orientation.SOUTH: (0, 0.3),
            }
            dx, dy = dir_map.get(state['agent_dir'], (0, 0))
            ax.annotate('', xy=(ax_pos+dx, ay_pos+dy), xytext=(ax_pos, ay_pos),
                       arrowprops=dict(arrowstyle='->', color='blue', lw=2))
            ax.plot(ax_pos, ay_pos, 'b^', markersize=12)
        
        ax.set_xticks(range(4))
        ax.set_yticks(range(4))
        ax.invert_yaxis()  # (0,0) at top-left
    
    def plot_knowledge(self, ax):
        """Plot agent's knowledge base."""
        self._base_grid(ax)
        state = self.world.get_state()

        width,height = state['size']
        
        # Color cells based on knowledge
        for x in range(width):
            for y in range(height):
                cell = (x, y)
                
                if cell in self.agent.visited:
                    color, label = 'lightgreen', 'V'
                elif cell in self.agent.safe:
                    color, label = 'lightblue', 'S'
                elif cell in self.agent.pit_safe and cell in self.agent.wumpus_safe:
                    color, label = 'lightyellow', 'S?'
                elif cell in self.agent.pit_safe:
                    color, label = 'wheat', 'P+'
                elif cell in self.agent.wumpus_safe:
                    color, label = 'mistyrose', 'W+'
                else:
                    color, label = 'lightgray', '?'
                
                ax.add_patch(plt.Rectangle((x-0.5, y-0.5), 1, 1, 
                                           facecolor=color, edgecolor='black'))
                ax.text(x, y, label, ha='center', va='center', fontsize=10)
        
        # Mark stench locations
        for sx, sy in self.agent.stench_at:
            ax.text(sx+0.3, sy-0.3, 'ST', ha='center', va='center', 
                   fontsize=7, color='purple', fontweight='bold')
        
        # Mark agent position
        agent_x, agent_y = self.agent.pos
        ax.plot(agent_x, agent_y, 'r*', markersize=18)
        
        ax.set_xticks(range(width))
        ax.set_yticks(range(height))
        ax.invert_yaxis()
        
    
        ax.text(
            0.5, 0.03,
            'V=Visited  S=Safe  P+=Pit-safe  W+=Wumpus-safe  ?=Unknown',
            transform=ax.transAxes,
            ha='center',
            fontsize=8,
            bbox=dict(
                facecolor='orange',
                alpha=0.8,
                edgecolor='none'
            )
        )

    
    def plot_info(self, ax, action=None, percept=None):
        """Plot game info and status."""
        ax.clear()
        ax.axis('off')
        ax.set_title('Game Status')
        
        state = self.world.get_state()
        
        info_lines = [
            f"Step: {self.step_count}",
            f"Position: {self.agent.pos}",
            f"Facing: {Orientation(self.agent.orientation).name}",
            f"Has Gold: {state['has_gold']}",
            f"Has Arrow: {state['has_arrow']}",
            f"Wumpus Alive: {state['wumpus_alive']}",
            f"Score: {state['score']}",
            #f"Size: {state['size']}",
            "",
        ]
        
        if action is not None:
            info_lines.append(f"Action: {Actions(action).name}")
        
        if percept:
            percept_list = []
            if percept.get(Percepts.BREEZE): percept_list.append('Breeze')
            if percept.get(Percepts.STENCH): percept_list.append('Stench')
            if percept.get(Percepts.GLITTER): percept_list.append('Glitter')
            if percept.get(Percepts.BUMP): percept_list.append('Bump')
            if percept.get(Percepts.SCREAM): percept_list.append('Scream')
            info_lines.append(f"Percepts: {', '.join(percept_list) if percept_list else 'None'}")
        
        info_lines.extend([
            "",
            f"Cells Visited: {len(self.agent.visited)}",
            f"Known Safe: {len(self.agent.safe)}",
        ])
        
        y_pos = 0.92
        for line in info_lines:
            ax.text(0.05, y_pos, line, transform=ax.transAxes, 
                   fontsize=10, verticalalignment='top', fontfamily='monospace')
            y_pos -= 0.075
    
    def visualize(self, action=None, percept=None):
        """Create full visualization."""
        fig, axes = plt.subplots(1, 3, figsize=(14, 5))
        
        self.plot_world(axes[0])
        self.plot_knowledge(axes[1])
        self.plot_info(axes[2], action, percept)
        
        plt.tight_layout()
        return fig
    
    def update_path(self):
        """Update path history."""
        if self.agent.pos != self.path_history[-1]:
            self.path_history.append(self.agent.pos)



class StepSimulator:
    """Run simulation step by step with visualization."""
    
    def __init__(self, size=(4,4), seed=None):
        self.size = size
        self.seed = seed
        self.playing = False  # Add playing flag to the simulator itself
        self.reset()
    
    def reset(self):
        """Initialize a new game."""
        self.agent = Agent(size=self.size)
        self.agent.new_episode()
        
        self.world = WumpusWorld(size = self.size, seed=self.seed)
        self.percept = self.world.get_percept()
        
        self.viz = WumpusVisualizer(self.world, self.agent)
        
        self.done = False
        self.last_action = None
    
    def step(self):
        """Execute one step and return visualization."""
        if self.done:
            return None, "Game Over"
        
        self.viz.step_count += 1
        
        # Get action from agent
        action = self.agent.get_action(self.percept, reward=0)
        self.last_action = action
        
        # Execute in environment
        self.percept, reward, self.done, info = self.world.step(action)
        
        # Update visualization
        self.viz.update_path()
        
        # Create visualization
        fig = self.viz.visualize(action, self.percept)
        
        # Determine status
        state = self.world.get_state()
        if self.done:
            if not state['agent_alive']:
                status = f"DEAD - {info.get('reason', 'unknown')}"
            elif state['has_gold']:
                status = f"WON! Score: {state['score']}"
            else:
                status = f"Escaped (no gold). Score: {state['score']}"
        else:
            status = f"Running... Score: {state['score']}"
        
        return fig, status
    
    def run_all(self, max_steps=50, delay=0.4):
        """Run entire simulation with animation - pausable version."""
        self.playing = True  # Set playing flag
        
        for step in range(max_steps):
            if not self.playing:  # Check if paused
                break
                
            clear_output(wait=True)
            fig, status = self.step()
            if fig:
                display(fig)
                plt.close(fig)  # Prevent memory buildup
            print(f"\nStatus: {status}")
            
            if self.done:
                self.playing = False
                break
            
            time.sleep(delay)
    
    def run_and_save_gif(sim, filename="wumpus_sim.gif", max_steps=50, delay=0.4):
        frames = []
    
        for step in range(max_steps):
            clear_output(wait=True)
            fig, status = sim.step()
            if fig:
                display(fig)
    
                # --- Capture figure to PNG in memory ---
                buf = io.BytesIO()
                fig.savefig(buf, format='png')
                buf.seek(0)
                image = imageio.imread(buf)
                frames.append(image)
                buf.close()
    
                plt.close(fig)
    
            print(f"\nStep {step+1}: {status}")
            if sim.done:
                break
            time.sleep(delay)
    
        # Save GIF
        imageio.mimsave(filename, frames, duration=delay)
        print(f"Saved GIF as {filename}")