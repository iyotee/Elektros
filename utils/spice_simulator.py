#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPICE simulation utilities for Bode analysis
"""

import os
import math
import cmath
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

# PySpice imports (optional)
SIM_AVAILABLE = True
try:
    from PySpice.Spice.NgSpice.Shared import NgSpiceShared
    from PySpice.Spice.Netlist import Circuit
    from PySpice.Unit import u_V, u_Hz, u_A, u_Ohm, u_F, u_H
    from PySpice.Spice.BasicElement import Resistor, Capacitor, Inductor, VoltageSource, CurrentSource
    from PySpice.Spice.Semiconductor import Diode, Mosfet
except ImportError:
    SIM_AVAILABLE = False


class BodeAnalyzer:
    """Performs Bode analysis on SPICE netlists"""
    
    def __init__(self):
        self.available = SIM_AVAILABLE
    
    def analyze_netlist(self, 
                       netlist_path: str,
                       input_node: str = "in",
                       output_node: str = "out",
                       start_freq: float = 1.0,
                       stop_freq: float = 1e6,
                       points_per_decade: int = 50) -> Dict[str, Any]:
        """
        Perform Bode analysis on a SPICE netlist
        
        Args:
            netlist_path: Path to SPICE netlist file
            input_node: Name of input node
            output_node: Name of output node
            start_freq: Start frequency in Hz
            stop_freq: Stop frequency in Hz
            points_per_decade: Number of points per decade
            
        Returns:
            Dictionary containing analysis results
        """
        if not self.available:
            return {
                "available": False,
                "note": "PySpice/ngspice not available. Install with: pip install PySpice"
            }
        
        if not os.path.exists(netlist_path):
            return {
                "available": False,
                "note": f"Netlist file not found: {netlist_path}"
            }
        
        try:
            return self._run_analysis(
                netlist_path, input_node, output_node,
                start_freq, stop_freq, points_per_decade
            )
        except Exception as e:
            return {
                "available": False,
                "note": f"Simulation failed: {str(e)}"
            }
    
    def _run_analysis(self, 
                     netlist_path: str,
                     input_node: str,
                     output_node: str,
                     start_freq: float,
                     stop_freq: float,
                     points_per_decade: int) -> Dict[str, Any]:
        """Run the actual SPICE analysis"""
        
        # Create circuit and include the netlist
        circuit = Circuit("Bode Analysis")
        
        # Read and include the netlist file
        with open(netlist_path, 'r') as f:
            netlist_content = f.read()
        
        # Add the netlist content to the circuit
        # This is a simplified approach - in practice, you might need to parse
        # the netlist and add components individually
        circuit.include(netlist_path)
        
        # Create simulator
        simulator = circuit.simulator(temperature=25, nominal_temperature=25)
        
        # Run AC analysis
        analysis = simulator.ac(
            start_frequency=start_freq@u_Hz,
            stop_frequency=stop_freq@u_Hz,
            number_of_points=points_per_decade,
            variation='dec'
        )
        
        # Extract frequency data
        frequencies = [float(f) for f in analysis.frequency]
        
        # Check if required nodes exist
        if input_node not in analysis.nodes:
            return {
                "available": True,
                "note": f"Input node '{input_node}' not found in simulation results",
                "available_nodes": list(analysis.nodes.keys())
            }
        
        if output_node not in analysis.nodes:
            return {
                "available": True,
                "note": f"Output node '{output_node}' not found in simulation results",
                "available_nodes": list(analysis.nodes.keys())
            }
        
        # Extract node voltages
        input_voltage = analysis.nodes[input_node]
        output_voltage = analysis.nodes[output_node]
        
        # Calculate transfer function
        gains_db = []
        phases_deg = []
        
        for i, freq in enumerate(freqs):
            try:
                # Calculate complex transfer function
                h = complex(output_voltage[i]) / complex(input_voltage[i])
                
                # Convert to dB and degrees
                gain_db = 20.0 * math.log10(abs(h) + 1e-18)
                phase_deg = math.degrees(cmath.phase(h))
                
                gains_db.append(gain_db)
                phases_deg.append(phase_deg)
                
            except (ZeroDivisionError, ValueError, OverflowError):
                gains_db.append(float('nan'))
                phases_deg.append(float('nan'))
        
        # Find crossover frequency and phase margin
        crossover_freq, phase_margin = self._find_crossover(frequencies, gains_db, phases_deg)
        
        # Create sample data for preview
        sample_size = min(10, len(frequencies))
        sample_data = list(zip(
            frequencies[:sample_size],
            gains_db[:sample_size],
            phases_deg[:sample_size]
        ))
        
        return {
            "available": True,
            "note": "Bode analysis completed successfully",
            "frequencies": frequencies,
            "gains_db": gains_db,
            "phases_deg": phases_deg,
            "crossover_freq": crossover_freq,
            "phase_margin": phase_margin,
            "sample": sample_data
        }
    
    def _find_crossover(self, 
                       frequencies: List[float], 
                       gains_db: List[float], 
                       phases_deg: List[float]) -> Tuple[Optional[float], Optional[float]]:
        """Find crossover frequency and phase margin"""
        
        crossover_freq = None
        phase_margin = None
        
        # Find where gain crosses 0 dB
        for i in range(1, len(frequencies)):
            if gains_db[i-1] > 0 and gains_db[i] <= 0:
                # Linear interpolation to find exact crossover frequency
                f1, f2 = frequencies[i-1], frequencies[i]
                g1, g2 = gains_db[i-1], gains_db[i]
                
                # Interpolate frequency
                crossover_freq = f1 + (f2 - f1) * (0 - g1) / (g2 - g1)
                
                # Interpolate phase at crossover
                p1, p2 = phases_deg[i-1], phases_deg[i]
                phase_at_crossover = p1 + (p2 - p1) * (crossover_freq - f1) / (f2 - f1)
                
                # Calculate phase margin (180° - phase at crossover)
                phase_margin = 180.0 - phase_at_crossover
                break
        
        return crossover_freq, phase_margin


class SpiceNetlistParser:
    """Parser for SPICE netlist files"""
    
    def __init__(self):
        self.components = []
        self.nodes = set()
        self.analysis_commands = []
    
    def parse_file(self, filepath: str) -> Dict[str, Any]:
        """
        Parse a SPICE netlist file
        
        Args:
            filepath: Path to the netlist file
            
        Returns:
            Dictionary containing parsed netlist data
        """
        with open(filepath, 'r') as f:
            content = f.read()
        
        return self.parse_content(content)
    
    def parse_content(self, content: str) -> Dict[str, Any]:
        """
        Parse SPICE netlist content
        
        Args:
            content: Netlist content as string
            
        Returns:
            Dictionary containing parsed netlist data
        """
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('*') or line.startswith('#'):
                continue
            
            # Parse different types of lines
            if line.upper().startswith('.AC'):
                self.analysis_commands.append(self._parse_ac_command(line))
            elif line.upper().startswith('.END'):
                break
            else:
                # Parse component line
                component = self._parse_component_line(line)
                if component:
                    self.components.append(component)
        
        return {
            "components": self.components,
            "nodes": list(self.nodes),
            "analysis_commands": self.analysis_commands
        }
    
    def _parse_ac_command(self, line: str) -> Dict[str, Any]:
        """Parse .AC command"""
        parts = line.split()
        if len(parts) < 4:
            return {}
        
        return {
            "type": "AC",
            "variation": parts[1],
            "points": int(parts[2]),
            "start_freq": float(parts[3]),
            "stop_freq": float(parts[4]) if len(parts) > 4 else None
        }
    
    def _parse_component_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a component line"""
        parts = line.split()
        if len(parts) < 2:
            return None
        
        # Extract component type and nodes
        component_type = parts[0][0].upper()
        nodes = parts[1:-1]  # All parts except first and last
        
        # Add nodes to set
        self.nodes.update(nodes)
        
        return {
            "type": component_type,
            "name": parts[0],
            "nodes": nodes,
            "value": parts[-1] if parts else None
        }


class StabilityAnalyzer:
    """Analyzes circuit stability from Bode data"""
    
    def __init__(self):
        pass
    
    def analyze_stability(self, 
                         frequencies: List[float],
                         gains_db: List[float], 
                         phases_deg: List[float]) -> Dict[str, Any]:
        """
        Analyze circuit stability from Bode plot data
        
        Args:
            frequencies: List of frequencies
            gains_db: List of gains in dB
            phases_deg: List of phases in degrees
            
        Returns:
            Dictionary containing stability analysis
        """
        # Find crossover frequency
        crossover_freq, phase_margin = self._find_crossover(frequencies, gains_db, phases_deg)
        
        # Analyze stability
        is_stable = phase_margin is not None and phase_margin > 45  # 45° minimum phase margin
        
        # Find bandwidth
        bandwidth = self._find_bandwidth(frequencies, gains_db)
        
        # Find dominant poles and zeros
        poles, zeros = self._find_poles_zeros(frequencies, gains_db, phases_deg)
        
        return {
            "is_stable": is_stable,
            "crossover_freq": crossover_freq,
            "phase_margin": phase_margin,
            "bandwidth": bandwidth,
            "poles": poles,
            "zeros": zeros,
            "stability_grade": self._grade_stability(phase_margin)
        }
    
    def _find_crossover(self, frequencies, gains_db, phases_deg):
        """Find crossover frequency and phase margin"""
        for i in range(1, len(frequencies)):
            if gains_db[i-1] > 0 and gains_db[i] <= 0:
                # Linear interpolation
                f1, f2 = frequencies[i-1], frequencies[i]
                g1, g2 = gains_db[i-1], gains_db[i]
                p1, p2 = phases_deg[i-1], phases_deg[i]
                
                crossover_freq = f1 + (f2 - f1) * (0 - g1) / (g2 - g1)
                phase_at_crossover = p1 + (p2 - p1) * (crossover_freq - f1) / (f2 - f1)
                phase_margin = 180.0 - phase_at_crossover
                
                return crossover_freq, phase_margin
        
        return None, None
    
    def _find_bandwidth(self, frequencies, gains_db):
        """Find -3dB bandwidth"""
        # Find frequency where gain is -3dB below maximum
        max_gain = max(gains_db)
        target_gain = max_gain - 3.0
        
        for i in range(1, len(frequencies)):
            if gains_db[i-1] >= target_gain and gains_db[i] < target_gain:
                # Linear interpolation
                f1, f2 = frequencies[i-1], frequencies[i]
                g1, g2 = gains_db[i-1], gains_db[i]
                return f1 + (f2 - f1) * (target_gain - g1) / (g2 - g1)
        
        return None
    
    def _find_poles_zeros(self, frequencies, gains_db, phases_deg):
        """Find dominant poles and zeros (simplified)"""
        # This is a simplified implementation
        # Real pole/zero finding would require more sophisticated analysis
        poles = []
        zeros = []
        
        # Look for -20dB/decade slopes (poles) and +20dB/decade slopes (zeros)
        for i in range(1, len(frequencies) - 1):
            f1, f2, f3 = frequencies[i-1], frequencies[i], frequencies[i+1]
            g1, g2, g3 = gains_db[i-1], gains_db[i], gains_db[i+1]
            
            # Calculate slope
            slope1 = (g2 - g1) / (math.log10(f2) - math.log10(f1))
            slope2 = (g3 - g2) / (math.log10(f3) - math.log10(f2))
            
            # Detect poles (negative slope)
            if slope1 < -15 and slope2 < -15:  # -20dB/decade
                poles.append(f2)
            
            # Detect zeros (positive slope)
            if slope1 > 15 and slope2 > 15:  # +20dB/decade
                zeros.append(f2)
        
        return poles[:5], zeros[:5]  # Return top 5
    
    def _grade_stability(self, phase_margin):
        """Grade stability based on phase margin"""
        if phase_margin is None:
            return "Unknown"
        elif phase_margin > 60:
            return "Excellent"
        elif phase_margin > 45:
            return "Good"
        elif phase_margin > 30:
            return "Marginal"
        else:
            return "Poor"
