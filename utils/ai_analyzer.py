#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI analysis utilities using Hugging Face models
"""

import json
from typing import Dict, Any, List, Optional
import pandas as pd

# Transformers imports
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class AIAnalyzer:
    """AI-powered analysis of electronic circuits"""
    
    def __init__(self, model_id: str = "google/flan-t5-large", device: str = "cpu"):
        self.model_id = model_id
        self.device = device
        self.available = TRANSFORMERS_AVAILABLE
        self.pipeline = None
        
        if self.available:
            self._load_model()
    
    def _load_model(self):
        """Load the AI model"""
        try:
            if "flan" in self.model_id.lower() or "t5" in model_id.lower():
                self.pipeline = pipeline(
                    "text2text-generation",
                    model=self.model_id,
                    device=-1 if self.device == "cpu" else 0
                )
            else:
                self.pipeline = pipeline(
                    "text-generation",
                    model=self.model_id,
                    device=-1 if self.device == "cpu" else 0
                )
        except Exception as e:
            print(f"[WARN] Failed to load AI model {self.model_id}: {e}")
            self.available = False
    
    def analyze_circuit(self, 
                       project_name: str,
                       bom_df: pd.DataFrame,
                       netlist: Dict[str, Any],
                       operating_conditions: Dict[str, Dict[str, float]],
                       bode_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Perform AI analysis of the circuit
        
        Args:
            project_name: Name of the project
            bom_df: BOM DataFrame
            netlist: Netlist data
            operating_conditions: Operating conditions for components
            bode_data: Bode analysis results
            
        Returns:
            AI analysis text
        """
        if not self.available:
            return "AI analysis unavailable: transformers library not installed"
        
        prompt = self._build_analysis_prompt(
            project_name, bom_df, netlist, operating_conditions, bode_data
        )
        
        try:
            return self._generate_analysis(prompt)
        except Exception as e:
            return f"AI analysis failed: {str(e)}"
    
    def _build_analysis_prompt(self,
                              project_name: str,
                              bom_df: pd.DataFrame,
                              netlist: Dict[str, Any],
                              operating_conditions: Dict[str, Dict[str, float]],
                              bode_data: Optional[Dict[str, Any]]) -> str:
        """Build the analysis prompt for the AI model"""
        
        # Prepare BOM summary
        bom_summary = self._summarize_bom(bom_df)
        
        # Prepare SOA data
        soa_data = self._extract_soa_data(bom_df)
        
        # Prepare Bode summary
        bode_summary = self._summarize_bode(bode_data)
        
        # Build the prompt
        prompt = f"""
You are an expert electronic engineer. Analyze the following circuit design and provide a comprehensive technical report.

PROJECT: {project_name}

CIRCUIT OVERVIEW:
- Components: {len(netlist.get('components', []))}
- Nets: {len(netlist.get('nets', []))}

BOM SUMMARY:
{bom_summary}

SOA ANALYSIS:
{soa_data}

OPERATING CONDITIONS:
{json.dumps(operating_conditions, indent=2)}

SIMULATION RESULTS:
{bode_summary}

Please provide a structured analysis covering:

1. FUNCTIONAL ANALYSIS
   - Identify main functional blocks (power supply, signal processing, control, etc.)
   - Analyze component selection and values
   - Check for design inconsistencies

2. SAFETY & RELIABILITY
   - Review SOA compliance for critical components
   - Identify potential failure modes
   - Suggest improvements for robustness

3. PERFORMANCE ANALYSIS
   - Analyze frequency response and stability
   - Check for proper decoupling and filtering
   - Evaluate EMI/EMC considerations

4. DESIGN RECOMMENDATIONS
   - Suggest component alternatives
   - Recommend design improvements
   - Identify cost optimization opportunities

5. ACTION ITEMS
   - List 5 priority actions with specific recommendations
   - Include measurable criteria for success

Format your response in clear, technical Markdown with specific component references.
"""
        
        return prompt.strip()
    
    def _summarize_bom(self, bom_df: pd.DataFrame) -> str:
        """Create a summary of the BOM"""
        if bom_df.empty:
            return "No BOM data available"
        
        # Group by component type
        component_types = {}
        for _, row in bom_df.iterrows():
            ref = str(row.get('ref', '')).strip()
            value = str(row.get('value', '')).strip()
            mpn = str(row.get('mpn', '')).strip()
            
            if not ref:
                continue
            
            # Determine component type from reference
            comp_type = ref[0].upper()
            if comp_type not in component_types:
                component_types[comp_type] = []
            
            component_types[comp_type].append({
                'ref': ref,
                'value': value,
                'mpn': mpn
            })
        
        # Format summary
        summary = []
        for comp_type, components in component_types.items():
            summary.append(f"\n{comp_type} Components ({len(components)}):")
            for comp in components[:5]:  # Show first 5 of each type
                summary.append(f"  - {comp['ref']}: {comp['value']} ({comp['mpn']})")
            if len(components) > 5:
                summary.append(f"  ... and {len(components) - 5} more")
        
        return "\n".join(summary)
    
    def _extract_soa_data(self, bom_df: pd.DataFrame) -> str:
        """Extract SOA data from BOM"""
        soa_components = []
        
        for _, row in bom_df.iterrows():
            ref = str(row.get('ref', '')).strip()
            soa_json = row.get('soa_json', '')
            
            if not ref or not soa_json:
                continue
            
            try:
                soa_data = json.loads(soa_json)
                if soa_data:
                    soa_components.append({
                        'ref': ref,
                        'soa': soa_data
                    })
            except json.JSONDecodeError:
                continue
        
        if not soa_components:
            return "No SOA data available"
        
        # Format SOA data
        summary = []
        for comp in soa_components[:10]:  # Show first 10
            ref = comp['ref']
            soa = comp['soa']
            summary.append(f"\n{ref}:")
            for param, value in soa.items():
                summary.append(f"  - {param}: {value}")
        
        return "\n".join(summary)
    
    def _summarize_bode(self, bode_data: Optional[Dict[str, Any]]) -> str:
        """Summarize Bode analysis results"""
        if not bode_data:
            return "No simulation data available"
        
        if not bode_data.get('available', False):
            return f"Simulation unavailable: {bode_data.get('note', 'Unknown error')}"
        
        summary = []
        summary.append("Bode Analysis Results:")
        
        if 'crossover_freq' in bode_data and bode_data['crossover_freq']:
            summary.append(f"- Crossover frequency: {bode_data['crossover_freq']:.2f} Hz")
        
        if 'phase_margin' in bode_data and bode_data['phase_margin']:
            summary.append(f"- Phase margin: {bode_data['phase_margin']:.1f}°")
        
        if 'sample' in bode_data and bode_data['sample']:
            summary.append("- Sample data (freq, gain dB, phase °):")
            for freq, gain, phase in bode_data['sample'][:5]:
                summary.append(f"  - {freq:.2f} Hz: {gain:.2f} dB, {phase:.1f}°")
        
        return "\n".join(summary)
    
    def _generate_analysis(self, prompt: str) -> str:
        """Generate analysis using the AI model"""
        if not self.pipeline:
            return "AI model not loaded"
        
        try:
            if "flan" in self.model_id.lower() or "t5" in self.model_id.lower():
                # Text-to-text generation
                result = self.pipeline(
                    prompt,
                    max_new_tokens=1000,
                    do_sample=False,
                    temperature=0.3
                )
                return result[0]["generated_text"]
            else:
                # Text generation
                result = self.pipeline(
                    prompt,
                    max_new_tokens=1000,
                    do_sample=True,
                    temperature=0.4,
                    top_p=0.9,
                    pad_token_id=self.pipeline.tokenizer.eos_token_id
                )
                return result[0]["generated_text"]
        except Exception as e:
            return f"AI generation failed: {str(e)}"


class ReportGenerator:
    """Generates comprehensive reports"""
    
    def __init__(self):
        pass
    
    def generate_report(self,
                       project_name: str,
                       bom_df: pd.DataFrame,
                       netlist: Dict[str, Any],
                       operating_conditions: Dict[str, Dict[str, float]],
                       bode_data: Optional[Dict[str, Any]],
                       ai_analysis: str) -> str:
        """
        Generate a comprehensive report
        
        Args:
            project_name: Name of the project
            bom_df: BOM DataFrame
            netlist: Netlist data
            operating_conditions: Operating conditions
            bode_data: Bode analysis results
            ai_analysis: AI analysis text
            
        Returns:
            Complete report as Markdown string
        """
        report = []
        
        # Header
        report.append(f"# AI Circuit Analysis Report: {project_name}")
        report.append(f"*Generated on: {self._get_timestamp()}*")
        report.append("")
        
        # Executive Summary
        report.append("## Executive Summary")
        report.append(self._generate_executive_summary(bom_df, netlist, bode_data))
        report.append("")
        
        # Circuit Overview
        report.append("## Circuit Overview")
        report.append(self._generate_circuit_overview(netlist))
        report.append("")
        
        # Component Analysis
        report.append("## Component Analysis")
        report.append(self._generate_component_analysis(bom_df))
        report.append("")
        
        # SOA Analysis
        report.append("## Safe Operating Area (SOA) Analysis")
        report.append(self._generate_soa_analysis(bom_df, operating_conditions))
        report.append("")
        
        # Simulation Results
        if bode_data:
            report.append("## Simulation Results")
            report.append(self._generate_simulation_section(bode_data))
            report.append("")
        
        # AI Analysis
        report.append("## AI Engineering Analysis")
        report.append(ai_analysis)
        report.append("")
        
        # Recommendations
        report.append("## Recommendations Summary")
        report.append(self._extract_recommendations(ai_analysis))
        report.append("")
        
        return "\n".join(report)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _generate_executive_summary(self, bom_df: pd.DataFrame, netlist: Dict[str, Any], bode_data: Optional[Dict[str, Any]]) -> str:
        """Generate executive summary"""
        summary = []
        
        # Basic stats
        summary.append(f"- **Total Components:** {len(netlist.get('components', []))}")
        summary.append(f"- **Total Nets:** {len(netlist.get('nets', []))}")
        summary.append(f"- **BOM Items:** {len(bom_df)}")
        
        # SOA compliance
        soa_checked = sum(1 for _, row in bom_df.iterrows() if row.get('soa_json'))
        summary.append(f"- **SOA Analyzed:** {soa_checked}/{len(bom_df)} components")
        
        # Simulation status
        if bode_data and bode_data.get('available'):
            summary.append(f"- **Simulation:** Completed successfully")
            if bode_data.get('crossover_freq'):
                summary.append(f"- **Crossover Frequency:** {bode_data['crossover_freq']:.2f} Hz")
        else:
            summary.append(f"- **Simulation:** Not available")
        
        return "\n".join(summary)
    
    def _generate_circuit_overview(self, netlist: Dict[str, Any]) -> str:
        """Generate circuit overview section"""
        components = netlist.get('components', [])
        
        # Group by component type
        by_type = {}
        for comp in components:
            ref = comp.get('ref', '')
            if ref:
                comp_type = ref[0].upper()
                if comp_type not in by_type:
                    by_type[comp_type] = []
                by_type[comp_type].append(comp)
        
        overview = []
        for comp_type, comps in by_type.items():
            overview.append(f"**{comp_type} Components ({len(comps)}):**")
            for comp in comps[:5]:  # Show first 5
                ref = comp.get('ref', '')
                value = comp.get('value', '')
                overview.append(f"- {ref}: {value}")
            if len(comps) > 5:
                overview.append(f"- ... and {len(comps) - 5} more")
            overview.append("")
        
        return "\n".join(overview)
    
    def _generate_component_analysis(self, bom_df: pd.DataFrame) -> str:
        """Generate component analysis section"""
        analysis = []
        
        # Analyze component distribution
        by_type = {}
        for _, row in bom_df.iterrows():
            ref = str(row.get('ref', '')).strip()
            if ref:
                comp_type = ref[0].upper()
                if comp_type not in by_type:
                    by_type[comp_type] = []
                by_type[comp_type].append(row)
        
        for comp_type, comps in by_type.items():
            analysis.append(f"### {comp_type} Components")
            analysis.append(f"Count: {len(comps)}")
            
            # Check for missing data
            missing_mpn = sum(1 for comp in comps if not str(comp.get('mpn', '')).strip())
            missing_datasheet = sum(1 for comp in comps if not str(comp.get('datasheet', '')).strip())
            
            if missing_mpn > 0:
                analysis.append(f"- Missing MPN: {missing_mpn}/{len(comps)}")
            if missing_datasheet > 0:
                analysis.append(f"- Missing datasheet: {missing_datasheet}/{len(comps)}")
            
            analysis.append("")
        
        return "\n".join(analysis)
    
    def _generate_soa_analysis(self, bom_df: pd.DataFrame, operating_conditions: Dict[str, Dict[str, float]]) -> str:
        """Generate SOA analysis section"""
        analysis = []
        
        soa_components = []
        for _, row in bom_df.iterrows():
            ref = str(row.get('ref', '')).strip()
            soa_json = row.get('soa_json', '')
            
            if ref and soa_json:
                try:
                    soa_data = json.loads(soa_json)
                    soa_components.append((ref, soa_data))
                except json.JSONDecodeError:
                    continue
        
        if not soa_components:
            analysis.append("No SOA data available for analysis.")
            return "\n".join(analysis)
        
        analysis.append(f"SOA data available for {len(soa_components)} components:")
        analysis.append("")
        
        for ref, soa_data in soa_components:
            analysis.append(f"### {ref}")
            analysis.append("**Extracted SOA Limits:**")
            for param, value in soa_data.items():
                analysis.append(f"- {param}: {value}")
            
            # Check against operating conditions
            if ref in operating_conditions:
                analysis.append("**Operating Conditions:**")
                for param, value in operating_conditions[ref].items():
                    analysis.append(f"- {param}: {value}")
                
                # Simple compliance check
                analysis.append("**Compliance Check:**")
                for param, value in operating_conditions[ref].items():
                    soa_param = param + "_max"
                    if soa_param in soa_data:
                        limit = soa_data[soa_param]
                        if value > limit:
                            analysis.append(f"- ❌ {param}={value} > {limit} (EXCEEDED)")
                        elif value > 0.8 * limit:
                            analysis.append(f"- ⚠️ {param}={value} close to limit {limit}")
                        else:
                            analysis.append(f"- ✅ {param}={value} OK (limit {limit})")
            else:
                analysis.append("No operating conditions specified.")
            
            analysis.append("")
        
        return "\n".join(analysis)
    
    def _generate_simulation_section(self, bode_data: Dict[str, Any]) -> str:
        """Generate simulation results section"""
        section = []
        
        if not bode_data.get('available', False):
            section.append(f"Simulation unavailable: {bode_data.get('note', 'Unknown error')}")
            return "\n".join(section)
        
        section.append("### Bode Analysis Results")
        
        if 'crossover_freq' in bode_data and bode_data['crossover_freq']:
            section.append(f"- **Crossover Frequency:** {bode_data['crossover_freq']:.2f} Hz")
        
        if 'phase_margin' in bode_data and bode_data['phase_margin']:
            section.append(f"- **Phase Margin:** {bode_data['phase_margin']:.1f}°")
            
            # Stability assessment
            pm = bode_data['phase_margin']
            if pm > 60:
                stability = "Excellent"
            elif pm > 45:
                stability = "Good"
            elif pm > 30:
                stability = "Marginal"
            else:
                stability = "Poor"
            section.append(f"- **Stability:** {stability}")
        
        if 'sample' in bode_data and bode_data['sample']:
            section.append("### Sample Data")
            section.append("| Frequency (Hz) | Gain (dB) | Phase (°) |")
            section.append("|----------------|-----------|-----------|")
            for freq, gain, phase in bode_data['sample'][:10]:
                section.append(f"| {freq:.2f} | {gain:.2f} | {phase:.1f} |")
        
        return "\n".join(section)
    
    def _extract_recommendations(self, ai_analysis: str) -> str:
        """Extract recommendations from AI analysis"""
        # This is a simple extraction - in practice, you might use more sophisticated NLP
        lines = ai_analysis.split('\n')
        recommendations = []
        
        in_recommendations = False
        for line in lines:
            line = line.strip()
            if 'action' in line.lower() or 'recommendation' in line.lower():
                in_recommendations = True
                continue
            
            if in_recommendations and line:
                if line.startswith('-') or line.startswith('*') or line.startswith('1.') or line.startswith('2.'):
                    recommendations.append(line)
                elif line.startswith('#'):
                    break
        
        if recommendations:
            return '\n'.join(recommendations)
        else:
            return "No specific recommendations found in AI analysis."
