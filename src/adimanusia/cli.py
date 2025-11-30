#!/usr/bin/env python
"""
Command Line Interface for adimanusia Lattice Climbing Simulation.

Usage:
    adimanusia case1              # The Pump Clock
    adimanusia case2              # The Crux Roulette
    adimanusia case3              # The Labyrinth
    adimanusia case4              # The Redpoint Crux
    adimanusia --all              # Run all scenarios
    adimanusia --config my.txt    # Custom config
"""

import argparse
import sys
import multiprocessing
from pathlib import Path

from .core.lattice import LatticeWall
from .core.agent import Climber
from .core.solver import Solver
from .io.config_manager import ConfigManager, AgentConfig
from .io.data_handler import DataHandler
from .visualization.animator import Animator
from .utils.logger import SimulationLogger
from .utils.timer import Timer


def print_header():
    """Print CLI header."""
    print("\n" + "=" * 65)
    print("   adimanusia: Lattice Climbing Agent-Based Model v0.0.1")
    print("=" * 65)
    print("   Greedy vs Prudent: Who reads the route better?")
    print("   MIT License | Sandy H.S. Herho & Freden M. Sembiring-Milala")
    print("=" * 65 + "\n")


def normalize_name(name: str) -> str:
    """Clean scenario name for filenames."""
    clean = name.lower()
    for char in [' - ', '-', ' ']:
        clean = clean.replace(char, '_')
    clean = ''.join(c for c in clean if c.isalnum() or c == '_')
    while '__' in clean:
        clean = clean.replace('__', '_')
    return clean.strip('_')


def setup_wall(config: dict) -> LatticeWall:
    """Create and configure wall from config."""
    wall = LatticeWall(
        height=config.get('wall_height', 40),
        width=config.get('wall_width', 20),
        base_terrain=config.get('base_terrain', 0.35),
        seed=config.get('seed')
    )
    
    scenario = config.get('scenario_type', 'custom')
    
    if scenario == 'pump_clock':
        wall.set_pump_clock_scenario()
    elif scenario == 'crux_roulette':
        wall.set_crux_roulette_scenario()
    elif scenario == 'labyrinth':
        wall.set_labyrinth_scenario()
    elif scenario == 'redpoint_crux':
        wall.set_redpoint_crux_scenario()
    
    return wall


def setup_agents(config: dict) -> list:
    """Create agents from config."""
    agents = []
    
    for ac in config.get('agents', []):
        if isinstance(ac, AgentConfig):
            agent = Climber(
                name=ac.name,
                energy=ac.energy,
                policy=ac.policy,
                lookahead=ac.lookahead,
                alpha=ac.alpha,
                beta=ac.beta,
                color=ac.color
            )
        elif isinstance(ac, dict):
            agent = Climber(
                name=ac['name'],
                energy=ac['energy'],
                policy=ac['policy'],
                lookahead=ac.get('lookahead', 5),
                alpha=ac.get('alpha', 0.5),
                beta=ac.get('beta', 0.3),
                color=ac.get('color')
            )
        else:
            continue
        agents.append(agent)
    
    return agents


def run_scenario(
    config: dict,
    output_dir: str = "outputs",
    verbose: bool = True,
    save_csv: bool = True,
    save_netcdf: bool = True,
    save_png: bool = True,
    save_gif: bool = True,
    n_cores: int = None
):
    """Run a complete simulation scenario."""
    scenario_name = config.get('scenario_name', 'Custom')
    clean_name = normalize_name(scenario_name)
    grade = config.get('grade', '5.10')
    
    if verbose:
        print(f"\n{'=' * 65}")
        print(f" SCENARIO: {scenario_name} ({grade})")
        print(f"{'=' * 65}")
    
    logger = SimulationLogger(clean_name, "logs", verbose)
    timer = Timer()
    timer.start("total")
    
    try:
        logger.log_parameters(config)
        
        # [1/6] Setup wall
        with timer.time_section("wall_setup"):
            if verbose:
                print(f"\n[1/6] Setting up wall...")
            
            wall = setup_wall(config)
            
            if verbose:
                print(f"      {wall}")
                print(f"      Description: {wall.scenario_description}")
        
        # [2/6] Setup agents
        with timer.time_section("agent_setup"):
            if verbose:
                print(f"\n[2/6] Initializing climbers...")
            
            agents = setup_agents(config)
            
            if verbose:
                for agent in agents:
                    print(f"      {agent.name}: E={agent.max_energy}, "
                          f"policy={agent.policy.value}, k={agent.lookahead}")
        
        # [3/6] Run simulation
        with timer.time_section("simulation"):
            if verbose:
                print(f"\n[3/6] Running simulation...")
            
            solver = Solver(
                max_steps=config.get('max_steps', 80),
                n_cores=n_cores,
                verbose=verbose
            )
            
            result = solver.solve(wall, agents)
        
        logger.log_results(result.agent_results)
        
        # [4/6] Save data
        with timer.time_section("data_save"):
            if verbose:
                print(f"\n[4/6] Saving data...")
            
            if save_csv or save_netcdf:
                DataHandler.save_all(
                    output_dir=output_dir,
                    result=result,
                    config=config,
                    prefix=clean_name,
                    save_csv=save_csv,
                    save_netcdf=save_netcdf
                )
                
                if verbose and save_csv:
                    print(f"      CSV saved to {output_dir}/csv/")
                if verbose and save_netcdf:
                    print(f"      NetCDF saved to {output_dir}/netcdf/")
        
        # [5/6] Visualizations
        with timer.time_section("visualization"):
            if verbose:
                print(f"\n[5/6] Creating visualizations...")
            
            animator = Animator(
                fps=config.get('animation_fps', 12),
                dpi=config.get('animation_dpi', 100)
            )
            
            if save_png:
                if verbose:
                    print("      Generating summary plot...")
                
                fig_dir = Path(output_dir) / "figs"
                fig_dir.mkdir(parents=True, exist_ok=True)
                
                png_file = fig_dir / f"{clean_name}_summary.png"
                animator.create_static_plot(result, str(png_file), scenario_name)
                
                if verbose:
                    print(f"      Saved: {png_file}")
            
            if save_gif:
                if verbose:
                    print("      Generating animation...")
                
                gif_dir = Path(output_dir) / "gifs"
                gif_dir.mkdir(parents=True, exist_ok=True)
                
                gif_file = gif_dir / f"{clean_name}_animation.gif"
                animator.create_animation(result, str(gif_file), scenario_name)
                
                if verbose:
                    print(f"      Saved: {gif_file}")
        
        timer.stop("total")
        logger.log_timing(timer.get_times())
        
        # [6/6] Summary
        if verbose:
            print(f"\n[6/6] RESULTS")
            print(f"{'=' * 65}")
            
            # Show comparative results
            for name, metrics in result.agent_results.items():
                status = metrics['status']
                height = metrics['final_height']
                max_h = metrics['max_height']
                pct = (height / max_h * 100) if max_h > 0 else 0
                e_used = metrics['energy_used']
                e_init = metrics['initial_energy']
                
                status_sym = "✓" if status == "Topped Out" else "✗"
                
                print(f"\n  {status_sym} {name}:")
                print(f"      Status: {status}")
                print(f"      Height: {height}/{max_h} ({pct:.0f}%)")
                print(f"      Energy: {e_used:.1f}/{e_init:.1f} used")
                if metrics.get('height_efficiency', 0) > 0:
                    print(f"      Efficiency: {metrics['energy_efficiency']:.2f} height/energy")
            
            # Winner announcement
            heights = [(name, m['final_height']) for name, m in result.agent_results.items()]
            heights.sort(key=lambda x: x[1], reverse=True)
            
            if heights[0][1] > heights[1][1]:
                winner = heights[0][0]
                print(f"\n  🏆 Winner: {winner}")
            elif heights[0][1] == heights[1][1]:
                # Tie-break by energy efficiency
                eff = [(name, m['energy_efficiency']) for name, m in result.agent_results.items()]
                eff.sort(key=lambda x: x[1], reverse=True)
                print(f"\n  🤝 Tie on height! {eff[0][0]} wins on efficiency")
            
            print(f"\n  Total time: {timer.times.get('total', 0):.2f}s")
            print(f"{'=' * 65}\n")
    
    except Exception as e:
        logger.error(f"Simulation failed: {str(e)}")
        if verbose:
            print(f"\n ERROR: {str(e)}\n")
        raise
    
    finally:
        logger.finalize()
    
    return result


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='adimanusia: Lattice Climbing Agent-Based Model',
        epilog='Example: adimanusia case1'
    )
    
    parser.add_argument(
        'case',
        nargs='?',
        choices=['case1', 'case2', 'case3', 'case4'],
        help='Test case (1: Pump Clock, 2: Crux Roulette, 3: Labyrinth, 4: Redpoint Crux)'
    )
    
    parser.add_argument('--config', '-c', type=str, help='Custom config file')
    parser.add_argument('--all', '-a', action='store_true', help='Run all cases')
    parser.add_argument('--output-dir', '-o', type=str, default='outputs', help='Output directory')
    parser.add_argument('--cores', type=int, default=None, 
                       help=f'CPU cores (default: all = {multiprocessing.cpu_count()})')
    parser.add_argument('--quiet', '-q', action='store_true', help='Quiet mode')
    
    # Save options
    parser.add_argument('--save-csv', action='store_true', default=None)
    parser.add_argument('--save-netcdf', action='store_true', default=None)
    parser.add_argument('--save-png', action='store_true', default=None)
    parser.add_argument('--save-gif', action='store_true', default=None)
    parser.add_argument('--no-csv', action='store_true')
    parser.add_argument('--no-netcdf', action='store_true')
    parser.add_argument('--no-png', action='store_true')
    parser.add_argument('--no-gif', action='store_true')
    
    args = parser.parse_args()
    verbose = not args.quiet
    
    # Determine save options
    save_csv = not args.no_csv if args.save_csv is None else args.save_csv
    save_netcdf = not args.no_netcdf if args.save_netcdf is None else args.save_netcdf
    save_png = not args.no_png if args.save_png is None else args.save_png
    save_gif = not args.no_gif if args.save_gif is None else args.save_gif
    
    if any([args.save_csv, args.save_netcdf, args.save_png, args.save_gif]):
        save_csv = args.save_csv or False
        save_netcdf = args.save_netcdf or False
        save_png = args.save_png or False
        save_gif = args.save_gif or False
    
    if verbose:
        print_header()
    
    # Custom config
    if args.config:
        config = ConfigManager.load(args.config)
        run_scenario(config, args.output_dir, verbose, save_csv, save_netcdf, save_png, save_gif, args.cores)
    
    # All cases
    elif args.all:
        scenarios = ['pump_clock', 'crux_roulette', 'labyrinth', 'redpoint_crux']
        
        for i, scenario in enumerate(scenarios, 1):
            if verbose:
                print(f"\n{'='*65}")
                print(f" Running Case {i}/4: {scenario}")
                print(f"{'='*65}")
            
            config = ConfigManager.get_scenario_config(scenario)
            run_scenario(config, args.output_dir, verbose, save_csv, save_netcdf, save_png, save_gif, args.cores)
    
    # Single case
    elif args.case:
        case_map = {
            'case1': 'pump_clock',
            'case2': 'crux_roulette',
            'case3': 'labyrinth',
            'case4': 'redpoint_crux'
        }
        
        scenario = case_map[args.case]
        
        # Try to load config file first
        configs_dir = Path(__file__).parent.parent.parent / 'configs'
        cfg_file = configs_dir / f'{args.case}_{scenario}.txt'
        
        if cfg_file.exists():
            config = ConfigManager.load(str(cfg_file))
        else:
            config = ConfigManager.get_scenario_config(scenario)
        
        run_scenario(config, args.output_dir, verbose, save_csv, save_netcdf, save_png, save_gif, args.cores)
    
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == '__main__':
    main()
