"""
Visualization for Lattice Climbing Simulations.

Clean, minimal style with:
- Black/white grid for wall structure
- Subtle route lines for each climber
- Clear hold markers
- Professional climbing topo aesthetic
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from PIL import Image
import io

from ..core.solver import SimulationResult
from ..core.agent import ClimberStatus


class Animator:
    """Create static plots and animations for climbing simulations."""
    
    # Clean color scheme
    COLORS = {
        'background': '#FFFFFF',
        'grid': '#E0E0E0',
        'blank': '#2C2C2C',
        'hold_good': '#4CAF50',
        'hold_moderate': '#FFC107', 
        'hold_poor': '#FF9800',
        'hold_hard': '#F44336',
        'greedy': '#E53935',      # Red
        'prudent': '#1E88E5',     # Blue
        'summit': '#4CAF50',
        'stuck': '#FF9800',
        'pumped': '#9E9E9E',
    }
    
    def __init__(self, fps: int = 12, dpi: int = 100):
        self.fps = fps
        self.dpi = dpi
        plt.style.use('default')
    
    def create_static_plot(
        self,
        result: SimulationResult,
        filepath: str,
        title: str = ""
    ):
        """
        Create clean static summary plot.
        
        Layout:
        - Left: Wall grid with routes
        - Right: Energy chart + metrics table
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        wall = result.wall
        
        fig = plt.figure(figsize=(14, 10), facecolor=self.COLORS['background'])
        
        # Grid spec: wall on left (wider), stats on right
        gs = fig.add_gridspec(2, 2, width_ratios=[1.5, 1], height_ratios=[2, 1],
                             hspace=0.3, wspace=0.25)
        
        ax_wall = fig.add_subplot(gs[:, 0])
        ax_energy = fig.add_subplot(gs[0, 1])
        ax_table = fig.add_subplot(gs[1, 1])
        
        # === WALL PLOT ===
        self._draw_wall(ax_wall, result)
        
        # === ENERGY PLOT ===
        self._draw_energy_chart(ax_energy, result)
        
        # === METRICS TABLE ===
        self._draw_metrics_table(ax_table, result)
        
        # Title
        grade = wall.grade if hasattr(wall, 'grade') else '5.10'
        fig.suptitle(f"{title}\n{wall.scenario_description}", 
                    fontsize=14, fontweight='bold', y=0.98)
        
        plt.savefig(filepath, dpi=self.dpi, bbox_inches='tight',
                   facecolor=self.COLORS['background'], edgecolor='none')
        plt.close(fig)
    
    def _draw_wall(self, ax: plt.Axes, result: SimulationResult):
        """Draw climbing wall with routes."""
        wall = result.wall
        H, W = wall.height, wall.width
        
        ax.set_facecolor(self.COLORS['background'])
        
        # Draw grid
        for r in range(H + 1):
            ax.axhline(y=r - 0.5, color=self.COLORS['grid'], linewidth=0.5, zorder=1)
        for c in range(W + 1):
            ax.axvline(x=c - 0.5, color=self.COLORS['grid'], linewidth=0.5, zorder=1)
        
        # Draw holds as circles colored by quality
        for r in range(H):
            for c in range(W):
                q = wall.grid[r, c]
                
                if q < 0.08:  # Blank
                    color = self.COLORS['blank']
                    size = 80
                    marker = 's'  # Square for blank
                elif q >= 0.7:  # Jug
                    color = self.COLORS['hold_good']
                    size = 120
                    marker = 'o'
                elif q >= 0.4:  # Moderate
                    color = self.COLORS['hold_moderate']
                    size = 80
                    marker = 'o'
                elif q >= 0.2:  # Poor
                    color = self.COLORS['hold_poor']
                    size = 50
                    marker = 'o'
                else:  # Hard
                    color = self.COLORS['hold_hard']
                    size = 30
                    marker = 'o'
                
                ax.scatter(c, r, s=size, c=color, marker=marker, 
                          edgecolors='black', linewidths=0.5, zorder=2, alpha=0.8)
        
        # Draw routes
        for agent in result.agents:
            trajectory = result.trajectories[agent.name]
            policy = agent.policy.value
            color = self.COLORS.get(policy, '#888888')
            
            # Convert trajectory to line segments
            if len(trajectory) > 1:
                rows = [p[0] for p in trajectory]
                cols = [p[1] for p in trajectory]
                
                # Draw line
                ax.plot(cols, rows, color=color, linewidth=2, alpha=0.7, 
                       zorder=3, label=agent.name)
                
                # Start marker
                ax.scatter(cols[0], rows[0], s=150, c=color, marker='^',
                          edgecolors='white', linewidths=2, zorder=5)
                
                # End marker
                status = result.agent_results[agent.name]['status']
                end_marker = 'o' if status == 'Topped Out' else 'X'
                ax.scatter(cols[-1], rows[-1], s=150, c=color, marker=end_marker,
                          edgecolors='white', linewidths=2, zorder=5)
        
        # Summit line
        ax.axhline(y=H - 1, color=self.COLORS['summit'], linewidth=3, 
                  linestyle='--', alpha=0.5, zorder=1, label='Summit')
        
        # Formatting
        ax.set_xlim(-0.5, W - 0.5)
        ax.set_ylim(-0.5, H - 0.5)
        ax.set_aspect('equal')
        ax.set_xlabel('Column', fontsize=10)
        ax.set_ylabel('Height', fontsize=10)
        ax.set_title('Route Topo', fontsize=12, fontweight='bold')
        
        # Legend
        ax.legend(loc='upper left', framealpha=0.9, fontsize=9)
        
        # Add hold legend
        hold_legend = [
            mpatches.Patch(color=self.COLORS['hold_good'], label='Jug (q≥0.7)'),
            mpatches.Patch(color=self.COLORS['hold_moderate'], label='Moderate (q≥0.4)'),
            mpatches.Patch(color=self.COLORS['hold_poor'], label='Poor (q≥0.2)'),
            mpatches.Patch(color=self.COLORS['hold_hard'], label='Hard (q<0.2)'),
            mpatches.Patch(color=self.COLORS['blank'], label='Blank'),
        ]
        ax.legend(handles=hold_legend, loc='lower right', fontsize=8, framealpha=0.9)
    
    def _draw_energy_chart(self, ax: plt.Axes, result: SimulationResult):
        """Draw energy consumption over time."""
        ax.set_facecolor(self.COLORS['background'])
        
        for agent in result.agents:
            energy_hist = result.energy_histories[agent.name]
            policy = agent.policy.value
            color = self.COLORS.get(policy, '#888888')
            
            steps = range(len(energy_hist))
            ax.plot(steps, energy_hist, color=color, linewidth=2, 
                   label=f"{agent.name}", marker='o', markersize=3)
        
        ax.set_xlabel('Step', fontsize=10)
        ax.set_ylabel('Energy Remaining', fontsize=10)
        ax.set_title('Energy Consumption', fontsize=12, fontweight='bold')
        ax.legend(loc='upper right', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0)
    
    def _draw_metrics_table(self, ax: plt.Axes, result: SimulationResult):
        """Draw performance metrics table."""
        ax.axis('off')
        
        # Build table data
        columns = ['Climber', 'Status', 'Height', 'Energy Used', 'Efficiency']
        rows = []
        
        for agent in result.agents:
            m = result.agent_results[agent.name]
            status = '✓ Topped' if m['success'] else f"✗ {m['status']}"
            height = f"{m['final_height']}/{m['max_height']}"
            energy = f"{m['energy_used']:.1f}/{m['initial_energy']:.0f}"
            eff = f"{m['energy_efficiency']:.3f}"
            
            rows.append([agent.name, status, height, energy, eff])
        
        # Create table
        table = ax.table(
            cellText=rows,
            colLabels=columns,
            loc='center',
            cellLoc='center',
            colWidths=[0.2, 0.25, 0.18, 0.2, 0.17]
        )
        
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.8)
        
        # Style header
        for i in range(len(columns)):
            table[(0, i)].set_facecolor('#E0E0E0')
            table[(0, i)].set_text_props(fontweight='bold')
        
        # Color rows by agent
        for i, agent in enumerate(result.agents, 1):
            policy = agent.policy.value
            color = self.COLORS.get(policy, '#888888')
            for j in range(len(columns)):
                table[(i, j)].set_facecolor(color + '20')  # Light version
        
        ax.set_title('Performance Metrics', fontsize=12, fontweight='bold', pad=20)
    
    def create_animation(
        self,
        result: SimulationResult,
        filepath: str,
        title: str = ""
    ):
        """Create animated GIF of climbing simulation."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        wall = result.wall
        H, W = wall.height, wall.width
        
        # Get max steps
        max_steps = max(len(t) for t in result.trajectories.values())
        
        frames = []
        
        for step in range(max_steps + 1):
            fig, ax = plt.subplots(figsize=(10, 12), facecolor=self.COLORS['background'])
            
            # Draw wall grid
            ax.set_facecolor(self.COLORS['background'])
            
            for r in range(H + 1):
                ax.axhline(y=r - 0.5, color=self.COLORS['grid'], linewidth=0.5, zorder=1)
            for c in range(W + 1):
                ax.axvline(x=c - 0.5, color=self.COLORS['grid'], linewidth=0.5, zorder=1)
            
            # Draw holds
            for r in range(H):
                for c in range(W):
                    q = wall.grid[r, c]
                    
                    if q < 0.08:
                        color = self.COLORS['blank']
                        size = 60
                        marker = 's'
                    elif q >= 0.7:
                        color = self.COLORS['hold_good']
                        size = 100
                        marker = 'o'
                    elif q >= 0.4:
                        color = self.COLORS['hold_moderate']
                        size = 70
                        marker = 'o'
                    elif q >= 0.2:
                        color = self.COLORS['hold_poor']
                        size = 45
                        marker = 'o'
                    else:
                        color = self.COLORS['hold_hard']
                        size = 25
                        marker = 'o'
                    
                    ax.scatter(c, r, s=size, c=color, marker=marker,
                              edgecolors='black', linewidths=0.3, zorder=2, alpha=0.7)
            
            # Draw agent paths up to current step
            for agent in result.agents:
                trajectory = result.trajectories[agent.name]
                energy_hist = result.energy_histories[agent.name]
                policy = agent.policy.value
                color = self.COLORS.get(policy, '#888888')
                
                # Current position
                current_step = min(step, len(trajectory) - 1)
                current_pos = trajectory[current_step]
                current_energy = energy_hist[current_step]
                
                # Draw trail
                if current_step > 0:
                    rows = [p[0] for p in trajectory[:current_step + 1]]
                    cols = [p[1] for p in trajectory[:current_step + 1]]
                    ax.plot(cols, rows, color=color, linewidth=2, alpha=0.5, zorder=3)
                
                # Draw current position
                ax.scatter(current_pos[1], current_pos[0], s=250, c=color,
                          marker='o', edgecolors='white', linewidths=3, zorder=6)
                
                # Label
                label_y = current_pos[0] + 0.8
                ax.annotate(f"{agent.name}\nE:{current_energy:.0f}",
                           (current_pos[1], label_y),
                           fontsize=9, ha='center', fontweight='bold',
                           color=color, zorder=7)
            
            # Summit line
            ax.axhline(y=H - 1, color=self.COLORS['summit'], linewidth=3,
                      linestyle='--', alpha=0.5, zorder=1)
            
            ax.set_xlim(-0.5, W - 0.5)
            ax.set_ylim(-0.5, H + 1)
            ax.set_aspect('equal')
            ax.set_xlabel('Column', fontsize=10)
            ax.set_ylabel('Height', fontsize=10)
            ax.set_title(f"{title}\nStep {step}/{max_steps}", fontsize=12, fontweight='bold')
            
            # Save frame to buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=self.dpi, bbox_inches='tight',
                       facecolor=self.COLORS['background'])
            buf.seek(0)
            frames.append(Image.open(buf).copy())
            buf.close()
            plt.close(fig)
        
        # Add final frames (hold on result)
        for _ in range(self.fps):
            frames.append(frames[-1].copy())
        
        # Save GIF
        frames[0].save(
            filepath,
            save_all=True,
            append_images=frames[1:],
            duration=int(1000 / self.fps),
            loop=0,
            optimize=True
        )
