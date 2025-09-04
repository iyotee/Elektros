#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
KiCad AI Interactive Chat Application
A modern web interface for interactive circuit analysis
"""

import streamlit as st
import pandas as pd
import json
import os
import tempfile
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
import base64
import numpy as np
from typing import Dict, Any

# Import our modules
from utils.api_clients import APIManager
from utils.soa_extractor import SOAExtractor, SOAChecker
from utils.spice_simulator import BodeAnalyzer
try:
    from utils.ai_analyzer import AIAnalyzer, ReportGenerator
    AI_AVAILABLE = True
except Exception as e:
    print(f"⚠️ AI features not available: {e}")
    AI_AVAILABLE = False
    AIAnalyzer = None
    ReportGenerator = None
from kicad_ai_allinone import read_bom, read_netlist, load_operating_conditions

# Page configuration
st.set_page_config(
    page_title="KiCad AI Interactive Chat",
    page_icon="🔌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2c3e50;
        text-align: left;
        margin-bottom: 1rem;
        font-weight: 600;
        letter-spacing: -0.5px;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .ai-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .component-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f9f9f9;
    }
    .soa-warning {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
    .soa-ok {
        background-color: #e8f5e8;
        border-left: 4px solid #4caf50;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'project_data' not in st.session_state:
    st.session_state.project_data = {}
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = {}

def initialize_apis():
    """Initialize API clients with provided credentials"""
    # Nexar/Octopart credentials
    nexar_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjA5NzI5QTkyRDU0RDlERjIyRDQzMENBMjNDNkI4QjJFIiwidHlwIjoiYXQrand0In0.eyJuYmYiOjE3NTY5ODU4NjUsImV4cCI6MTc1NzA3MjI2NSwiaXNzIjoiaHR0cHM6Ly9pZGVudGl0eS5uZXhhci5jb20iLCJjbGllbnRfaWQiOiIxODEwYjk4ZC02NTYyLTQ5ZDgtOTNkMy0yMjM5NzFiZjZjZGMiLCJzdWIiOiJFNTIzREVBNy1BODU2LTRFRTUtQjM0Ny03RUI3OEE3N0E0NEUiLCJhdXRoX3RpbWUiOjE3NTY5ODU2OTAsImlkcCI6Ikdvb2dsZSIsInByaXZhdGVfY2xhaW1zX2lkIjoiZjhjNTcxYzctMDM1Mi00YjFkLWI5ZjYtYjQ1NTFiOGI3MjcwIiwicHJpdmF0ZV9jbGFpbXNfc2VjcmV0IjoibnNnNytsZG5RZ2tIMDlpcnJGN2xxQzVzb3RncEx5MVVTaGdOaWhOVktoWT0iLCJqdGkiOiI2NTdFMDFGRjU2NjUxRUY4M0YyNjVCRkE4NTYxOTI4NyIsInNpZCI6IjczRjNGRDBBNjFEQjk3MzRCNzQ1REQyN0VBMEY1NzNDIiwiaWF0IjoxNzU2OTg1ODY1LCJzY29wZSI6WyJvcGVuaWQiLCJ1c2VyLmFjY2VzcyIsInByb2ZpbGUiLCJlbWFpbCIsInVzZXIuZGV0YWlscyIsImRlc2lnbi5kb21haW4iLCJzdXBwbHkuZG9tYWluIl0sImFtciI6WyJleHRlcm5hbCJdfQ.eqCuD2fTetsg7yXAESGQEah5vONruj4zBlB_Vb0jAroIjl14bdpwRzWrC8nzdl7SkMSr8nPp3tGaO6hacuPGCSPdbS5vRoBMZM_Yh8b4m70IAzeDUevZiqtdGMSsIlvw4TzGZ6LLTr60cHg8hPPAuYr4h7j5gYr1axbycFvBU-2hQ2Sr09AnF_g_gKyLmNjOrfx_8UMIK5U5Y18goBKZvr-dWQPkK-MVy0deLAraj2GI6SqWCX9NHk2sLG5sSWhNLHecJl-WuNSjJexqpWfiArH7XwcU3nFaBCxxIJGrHs3ARhszeCbwc84pA5GFo3iM_PCW8JAdI9sPmj6aK6BdQQ"
    
    # Mouser credentials
    mouser_key = "7b994823-8625-4774-a4c6-bb16b95cc7e5"
    
    return APIManager(octopart_key=nexar_token, mouser_key=mouser_key)

def load_project_files(netlist_file, bom_file, operating_file=None):
    """Load and process KiCad project files"""
    try:
        # Save uploaded files temporarily
        # Use /tmp on Streamlit Cloud, tempfile on local
        if os.getenv("STREAMLIT_CLOUD"):
            temp_dir = "/tmp"
        else:
            temp_dir = tempfile.mkdtemp()
            # Save netlist
            netlist_path = os.path.join(temp_dir, netlist_file.name)
            with open(netlist_path, "wb") as f:
                f.write(netlist_file.getbuffer())
            
            # Save BOM
            bom_path = os.path.join(temp_dir, bom_file.name)
            with open(bom_path, "wb") as f:
                f.write(bom_file.getbuffer())
            
            # Save operating conditions if provided
            operating_path = None
            if operating_file:
                operating_path = os.path.join(temp_dir, operating_file.name)
                with open(operating_path, "wb") as f:
                    f.write(operating_file.getbuffer())
            
            # Check if files exist and are readable
            if not os.path.exists(netlist_path):
                raise FileNotFoundError(f"Netlist file not found: {netlist_path}")
            if not os.path.exists(bom_path):
                raise FileNotFoundError(f"BOM file not found: {bom_path}")
            
            # Read netlist
            st.info(f"Reading netlist: {netlist_file.name}")
            netlist = read_netlist(netlist_path)
            
            # Read BOM
            st.info(f"Reading BOM: {bom_file.name}")
            bom_df = read_bom(bom_path)
            
            # Read operating conditions if provided
            operating_conditions = {}
            if operating_path:
                operating_conditions = load_operating_conditions(operating_path)
            
            return {
                'netlist': netlist,
                'bom': bom_df,
                'operating_conditions': operating_conditions,
                'project_name': Path(netlist_file.name).stem if hasattr(netlist_file, 'name') else 'project'
            }
    except Exception as e:
        import traceback
        st.error(f"Error loading project files: {str(e)}")
        st.error(f"Full error: {traceback.format_exc()}")
        return None

def enrich_bom_with_apis(bom_df, api_manager):
    """Enrich BOM with API data"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    enriched_bom = bom_df.copy()
    
    for i, (_, row) in enumerate(bom_df.iterrows()):
        ref = str(row.get('ref', '')).strip()
        mpn = str(row.get('mpn', '')).strip()
        
        if mpn and ref:
            status_text.text(f"Enriching {ref} ({mpn})...")
            
            # Search for part data
            datasheet_url, spice_url = api_manager.search_part(mpn)
            
            if datasheet_url:
                enriched_bom.loc[enriched_bom['ref'] == ref, 'datasheet'] = datasheet_url
            if spice_url:
                enriched_bom.loc[enriched_bom['ref'] == ref, 'spice_model_url'] = spice_url
            
            progress_bar.progress((i + 1) / len(bom_df))
    
    status_text.text("BOM enrichment completed!")
    progress_bar.empty()
    status_text.empty()
    
    return enriched_bom

def analyze_soa(bom_df, operating_conditions):
    """Analyze SOA compliance"""
    soa_extractor = SOAExtractor()
    soa_checker = SOAChecker()
    
    soa_results = {}
    processed_count = 0
    skipped_count = 0
    
    # Debug: Print BOM info
    print(f"[DEBUG] SOA Analysis: BOM has {len(bom_df)} rows")
    print(f"[DEBUG] BOM columns: {list(bom_df.columns)}")
    print(f"[DEBUG] Operating conditions keys: {list(operating_conditions.keys())}")
    
    for _, row in bom_df.iterrows():
        # Try different possible column names for reference
        ref = None
        for col_name in ['ref', 'reference', 'designator', 'part', 'component']:
            if col_name in row.index:
                ref = str(row.get(col_name, '')).strip()
                if ref and ref != 'nan' and ref != '':
                    break
        
        if not ref:
            skipped_count += 1
            if skipped_count <= 3:  # Only show first 3 skipped rows
                print(f"[DEBUG] Skipping row {skipped_count}: Available columns: {list(row.index)}")
                print(f"[DEBUG] Row data: {row.to_dict()}")
            continue
            
        processed_count += 1
        print(f"[DEBUG] Processing component {processed_count}: {ref}")
        
        # Create estimated SOA data for all components
        value = str(row.get('value', '')).upper()
        mpn = str(row.get('mpn', '')).upper()
        
        # Estimate SOA based on component characteristics
        if any(keyword in value for keyword in ['V', 'A', 'W']):
            soa_data = {
                'Vds_max': 50.0,
                'Id_max': 1.0,
                'Pd_max': 1.0,
                'Vr_max': 30.0,
                'If_max': 1.0,
                'source': 'estimated'
            }
        elif any(keyword in mpn for keyword in ['MOSFET', 'TRANSISTOR', 'DIODE']):
            soa_data = {
                'Vds_max': 100.0,
                'Id_max': 2.0,
                'Pd_max': 2.0,
                'Vr_max': 50.0,
                'If_max': 2.0,
                'source': 'estimated'
            }
        else:
            soa_data = {
                'Vds_max': 30.0,
                'Id_max': 0.5,
                'Pd_max': 0.5,
                'Vr_max': 20.0,
                'If_max': 0.5,
                'source': 'estimated'
            }
        
        # Check compliance
        component_conditions = operating_conditions.get(ref, {})
        if not component_conditions:
            component_conditions = {
                'voltage': 5.0,
                'current': 0.1,
                'power': 0.5
            }
        
        compliance_results = soa_checker.check_compliance(soa_data, component_conditions)
        
        soa_results[ref] = {
            'soa_data': soa_data,
            'operating_conditions': component_conditions,
            'compliance': compliance_results
        }
    
    print(f"[DEBUG] SOA Analysis complete: {processed_count} processed, {skipped_count} skipped")
    return soa_results

def run_simulation(project_data):
    """Run basic circuit simulation"""
    try:
        # Basic simulation based on netlist analysis
        netlist = project_data['netlist']
        components = netlist.get('components', [])
        nets = netlist.get('nets', [])
        
        # Count component types
        component_counts = {}
        for comp in components:
            comp_type = comp.get('type', 'Unknown')
            component_counts[comp_type] = component_counts.get(comp_type, 0) + 1
        
        # Analyze power consumption
        power_consumption = 0
        voltage_sources = []
        
        for comp in components:
            comp_type = comp.get('type', '')
            value = comp.get('value', '')
            
            if comp_type == 'V':  # Voltage source
                try:
                    voltage = float(value.replace('V', ''))
                    voltage_sources.append(voltage)
                except:
                    voltage_sources.append(5.0)  # Default 5V
            elif comp_type == 'R':  # Resistor
                try:
                    resistance = float(value.replace('k', '000').replace('M', '000000'))
                    # Estimate current: V/R
                    if voltage_sources:
                        current = voltage_sources[0] / resistance
                        power_consumption += current * voltage_sources[0]
                except:
                    pass
        
        # Calculate basic metrics - use BOM count for unique components
        bom_df = project_data.get('bom', pd.DataFrame())
        total_components = len(bom_df) if not bom_df.empty else len(components)
        total_nets = len(nets)
        estimated_power = power_consumption if power_consumption > 0 else 0.1  # Default 100mW
        
        simulation_results = {
            'available': True,
            'note': 'Basic circuit analysis simulation',
            'total_components': total_components,
            'total_nets': total_nets,
            'component_counts': component_counts,
            'voltage_sources': voltage_sources,
            'estimated_power_consumption': estimated_power,
            'simulation_type': 'basic_analysis'
        }
        
        return simulation_results
        
    except Exception as e:
        return {
            'available': False,
            'note': f'Simulation failed: {str(e)}',
            'error': str(e)
        }

def run_ai_analysis(project_data, bode_data=None):
    """Run AI analysis on the project"""
    if not AI_AVAILABLE or not AIAnalyzer:
        return {"error": "AI features not available"}
        
    ai_analyzer = AIAnalyzer("google/flan-t5-large", "cuda")
    
    if not ai_analyzer.available:
        return {"error": "AI model failed to load"}
    
    analysis = ai_analyzer.analyze_circuit(
        project_data['project_name'],
        project_data['bom'],
        project_data['netlist'],
        project_data['operating_conditions'],
        bode_data
    )
    
    return analysis

def display_component_analysis(component_data, soa_results):
    """Display detailed component analysis"""
    ref = component_data['ref']
    value = component_data['value']
    mpn = component_data['mpn']
    
    with st.expander(f"🔧 {ref} - {value} ({mpn})", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Component Details:**")
            st.write(f"- Reference: {ref}")
            st.write(f"- Value: {value}")
            st.write(f"- MPN: {mpn}")
            
            if 'datasheet' in component_data and component_data['datasheet']:
                datasheet_url = component_data['datasheet']
                if datasheet_url.startswith('http'):
                    st.write("- Datasheet:")
                    st.link_button("📄 Open Datasheet", datasheet_url)
                else:
                    st.write(f"- Datasheet: {datasheet_url}")
        
        with col2:
            if ref in soa_results:
                soa_info = soa_results[ref]
                
                st.write("**SOA Analysis:**")
                
                if soa_info['soa_data']:
                    st.write("**Extracted Limits:**")
                    for param, value in soa_info['soa_data'].items():
                        st.write(f"- {param}: {value}")
                
                if soa_info['compliance']:
                    st.write("**Compliance Check:**")
                    for result in soa_info['compliance']:
                        if "❌" in result:
                            st.markdown(f'<div class="soa-warning">{result}</div>', unsafe_allow_html=True)
                        elif "⚠️" in result:
                            st.warning(result)
                        else:
                            st.markdown(f'<div class="soa-ok">{result}</div>', unsafe_allow_html=True)

def display_bode_analysis(bode_data):
    """Display Bode analysis results"""
    if not bode_data or not bode_data.get('available'):
        st.warning("Bode analysis not available")
        return
    
    st.subheader("📊 Bode Analysis Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if bode_data.get('crossover_freq'):
            st.metric("Crossover Frequency", f"{bode_data['crossover_freq']:.2f} Hz")
    
    with col2:
        if bode_data.get('phase_margin'):
            st.metric("Phase Margin", f"{bode_data['phase_margin']:.1f}°")
    
    with col3:
        if bode_data.get('phase_margin'):
            pm = bode_data['phase_margin']
            if pm > 60:
                stability = "Excellent"
                color = "green"
            elif pm > 45:
                stability = "Good"
                color = "blue"
            elif pm > 30:
                stability = "Marginal"
                color = "orange"
            else:
                stability = "Poor"
                color = "red"
            
            st.metric("Stability", stability)
    
    # Plot Bode diagram if data available
    if 'frequencies' in bode_data and 'gains_db' in bode_data:
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=bode_data['frequencies'],
            y=bode_data['gains_db'],
            mode='lines',
            name='Gain (dB)',
            line=dict(color='blue')
        ))
        
        fig.update_layout(
            title="Bode Plot - Gain vs Frequency",
            xaxis_title="Frequency (Hz)",
            yaxis_title="Gain (dB)",
            xaxis_type="log",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

def chat_interface():
    """Main chat interface"""
    # Header with logo and title
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image("logo.png", width=100)
    with col2:
        st.markdown('<h1 class="main-header">KiCad AI Interactive Chat</h1>', unsafe_allow_html=True)
        st.markdown("**Version 1.0** | **Author:** Jérémy Noverraz | **SwissLabs, Lausanne**")
    
    # Sidebar for file uploads
    with st.sidebar:
        # Logo and branding
        st.image("logo.png", width=200)
        st.markdown("### KiCad AI Interactive Chat")
        st.markdown("**Version 1.0**")
        st.markdown("**Author:** Jérémy Noverraz")
        st.markdown("**SwissLabs, Lausanne**")
        st.markdown("[![GitHub](https://img.shields.io/badge/GitHub-iyotee-blue?style=flat&logo=github)](https://github.com/iyotee)")
        st.markdown("---")
        
        st.header("📁 Project Files")
        
        # File uploaders
        netlist_file = st.file_uploader(
            "Upload Netlist (.net/.xml)",
            type=['net', 'xml'],
            help="Upload your KiCad netlist file (XML or SPICE .net format)"
        )
        
        bom_file = st.file_uploader(
            "Upload BOM (.csv/.xml)",
            type=['csv', 'xml'],
            help="Upload your KiCad BOM file"
        )
        
        operating_file = st.file_uploader(
            "Upload Operating Conditions (.yaml)",
            type=['yaml', 'yml'],
            help="Upload operating conditions file (optional)"
        )
        
        # Load project button
        if st.button("🚀 Load Project", type="primary"):
            if netlist_file and bom_file:
                # Save uploaded files temporarily
                with tempfile.TemporaryDirectory() as temp_dir:
                    netlist_path = os.path.join(temp_dir, netlist_file.name)
                    bom_path = os.path.join(temp_dir, bom_file.name)
                    operating_path = None
                    
                    with open(netlist_path, "wb") as f:
                        f.write(netlist_file.getbuffer())
                    
                    with open(bom_path, "wb") as f:
                        f.write(bom_file.getbuffer())
                    
                    if operating_file:
                        operating_path = os.path.join(temp_dir, operating_file.name)
                        with open(operating_path, "wb") as f:
                            f.write(operating_file.getbuffer())
                    
                    # Load project data
                    project_data = load_project_files(netlist_file, bom_file, operating_file)
                    
                    if project_data:
                        st.session_state.project_data = project_data
                        st.success("Project loaded successfully!")
                        
                        # Initialize APIs and enrich BOM
                        with st.spinner("Enriching BOM with API data..."):
                            api_manager = initialize_apis()
                            enriched_bom = enrich_bom_with_apis(project_data['bom'], api_manager)
                            
                            # Debug: Show BOM columns and datasheet info
                            st.info(f"🔍 BOM columns: {list(enriched_bom.columns)}")
                            
                            # Also try to get datasheets from existing BOM data
                            datasheet_found = 0
                            for i, row in enriched_bom.iterrows():
                                # Check if datasheet is in original BOM data
                                if 'datasheet' in row and row['datasheet'] and str(row['datasheet']).strip():
                                    datasheet_found += 1
                                    continue  # Already has datasheet
                                
                                # Try to find datasheet in other columns
                                for col in ['datasheet_url', 'datasheet_path', 'pdf_url', 'documentation']:
                                    if col in row and row[col] and str(row[col]).strip():
                                        enriched_bom.loc[i, 'datasheet'] = str(row[col]).strip()
                                        datasheet_found += 1
                                        break
                            
                            st.info(f"📄 Found {datasheet_found} datasheets in BOM")
                            
                            st.session_state.project_data['bom'] = enriched_bom
                        
                        # Run simulation
                        with st.spinner("Running circuit simulation..."):
                            simulation_results = run_simulation(project_data)
                            st.session_state.analysis_results['simulation'] = simulation_results
                        
                        # Analyze SOA
                        with st.spinner("Analyzing SOA compliance..."):
                            soa_results = analyze_soa(enriched_bom, project_data['operating_conditions'])
                            st.session_state.analysis_results['soa'] = soa_results
                            
                            # Display SOA debug info
                            st.info(f"🔍 SOA Debug: Found {len(soa_results)} components with SOA data")
                            if len(soa_results) == 0:
                                st.warning("⚠️ No SOA data found. Check BOM structure and component references.")
                                with st.expander("Show BOM Debug Info"):
                                    st.write("BOM columns:", list(enriched_bom.columns))
                                    st.write("First 5 rows:")
                                    st.dataframe(enriched_bom.head())
                        
                        # Run AI analysis
                        with st.spinner("Running AI analysis..."):
                            ai_analysis = run_ai_analysis(project_data, simulation_results)
                            st.session_state.analysis_results['ai'] = ai_analysis
                        
                        st.success("Analysis completed!")
            else:
                st.error("Please upload both netlist and BOM files")
    
    # Main chat area
    if st.session_state.project_data:
        # Display project summary
        st.subheader("📋 Project Summary")
        
        project_data = st.session_state.project_data
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Components", len(project_data['netlist']['components']))
        with col2:
            st.metric("Nets", len(project_data['netlist']['nets']))
        with col3:
            st.metric("BOM Items", len(project_data['bom']))
        
        # Tabs for different views
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["💬 Chat", "🔧 Components", "📊 Analysis", "🎯 3D Visualization", "📄 Report"])
        
        with tab1:
            # Chat interface
            st.subheader("💬 Interactive Chat")
            
            # Display chat messages
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            
            # Chat input
            if prompt := st.chat_input("Ask me about your circuit..."):
                # Add user message
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # Generate AI response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        # Simple response generation based on prompt
                        response = generate_chat_response(prompt, project_data, st.session_state.analysis_results)
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
        
        with tab2:
            # Component analysis
            st.subheader("🔧 Component Analysis")
            
            for _, component in project_data['bom'].iterrows():
                display_component_analysis(component, st.session_state.analysis_results.get('soa', {}))
        
        with tab3:
            # Analysis results
            st.subheader("📊 Analysis Results")
            
            # Simulation Results
            if 'simulation' in st.session_state.analysis_results:
                st.subheader("⚡ Simulation Results")
                sim_results = st.session_state.analysis_results['simulation']
                
                if sim_results.get('available', False):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Components", sim_results.get('total_components', 0))
                    with col2:
                        st.metric("Total Nets", sim_results.get('total_nets', 0))
                    with col3:
                        st.metric("Power Consumption", f"{sim_results.get('estimated_power_consumption', 0):.2f}W")
                    
                    if sim_results.get('voltage_sources'):
                        st.write(f"**Voltage Sources:** {sim_results['voltage_sources']}")
                    
                    if sim_results.get('component_counts'):
                        st.write("**Component Distribution:**")
                        for comp_type, count in sim_results['component_counts'].items():
                            st.write(f"- {comp_type}: {count}")
                else:
                    st.warning(f"Simulation not available: {sim_results.get('note', 'Unknown error')}")
            
            # SOA Analysis
            if 'soa' in st.session_state.analysis_results:
                st.subheader("🛡️ SOA Analysis")
                soa_results = st.session_state.analysis_results['soa']
                
                for ref, soa_info in soa_results.items():
                    if soa_info['compliance']:
                        st.write(f"**{ref}:**")
                        for result in soa_info['compliance']:
                            if "❌" in result:
                                st.markdown(f'<div class="soa-warning">{result}</div>', unsafe_allow_html=True)
                            elif "⚠️" in result:
                                st.warning(result)
                            else:
                                st.markdown(f'<div class="soa-ok">{result}</div>', unsafe_allow_html=True)
            
            # AI Analysis
            if 'ai' in st.session_state.analysis_results:
                st.subheader("🤖 AI Analysis")
                st.markdown(st.session_state.analysis_results['ai'])
        
        with tab4:
            # 3D Visualization
            st.subheader("🎯 3D Circuit Visualization")
            
            if 'project_data' in st.session_state and st.session_state.project_data:
                project_data = st.session_state.project_data
                
                # 3D Circuit Layout
                st.subheader("🔧 3D Circuit Layout")
                circuit_3d = create_3d_circuit_visualization(project_data['netlist'], project_data['bom'])
                st.plotly_chart(circuit_3d, use_container_width=True)
                
                # 3D Power Analysis
                if 'simulation' in st.session_state.analysis_results:
                    st.subheader("⚡ 3D Power Analysis")
                    power_3d = create_3d_power_analysis(st.session_state.analysis_results['simulation'])
                    if power_3d:
                        st.plotly_chart(power_3d, use_container_width=True)
                    else:
                        st.warning("No simulation data available for 3D power visualization")
                
                # 3D SOA Analysis
                if 'soa' in st.session_state.analysis_results:
                    st.subheader("🛡️ 3D SOA Safety Analysis")
                    soa_3d = create_3d_soa_visualization(st.session_state.analysis_results['soa'])
                    if soa_3d:
                        st.plotly_chart(soa_3d, use_container_width=True)
                    else:
                        st.warning("No SOA data available for 3D visualization")
                
                # Interactive controls
                st.subheader("🎮 Interactive Controls")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🔄 Refresh 3D Views"):
                        st.rerun()
                
                with col2:
                    show_nets = st.checkbox("Show Net Connections", value=True)
                
                with col3:
                    show_labels = st.checkbox("Show Component Labels", value=True)
                
                # Legend
                st.subheader("📋 Component Legend")
                legend_data = {
                    'Resistors (R)': '#FF6B6B',
                    'Capacitors (C)': '#4ECDC4',
                    'Inductors (L)': '#45B7D1',
                    'Diodes (D)': '#96CEB4',
                    'Transistors (Q)': '#FFEAA7',
                    'ICs (U)': '#DDA0DD',
                    'Voltage Sources (V)': '#FFB347',
                    'Current Sources (I)': '#98D8C8'
                }
                
                for comp_type, color in legend_data.items():
                    st.markdown(f"<span style='color: {color}'>●</span> {comp_type}", unsafe_allow_html=True)
            else:
                st.info("Please upload and analyze your circuit files to see 3D visualizations")
        
        with tab5:
            # Full report
            st.subheader("📄 Full Report")
            
            if 'ai' in st.session_state.analysis_results:
                report_generator = ReportGenerator()
                # Pass SOA results to the report generator
                soa_count = len(st.session_state.analysis_results.get('soa', {}))
                simulation_data = st.session_state.analysis_results.get('simulation', {})
                
                full_report = report_generator.generate_report(
                    project_data['project_name'],
                    project_data['bom'],
                    project_data['netlist'],
                    project_data['operating_conditions'],
                    simulation_data,  # bode_data
                    st.session_state.analysis_results['ai'],
                    soa_count  # Add SOA count
                )
                
                st.markdown(full_report)
                
                # Download button
                st.download_button(
                    label="📥 Download Report",
                    data=full_report,
                    file_name=f"{project_data['project_name']}_analysis_report.md",
                    mime="text/markdown"
                )
    
    else:
        # Welcome screen
        st.markdown("""
        ## Welcome to KiCad AI Interactive Chat! 🚀
        
        This tool helps you analyze your KiCad designs with AI-powered insights.
        
        **Features:**
        - 🔍 Automatic BOM enrichment via Octopart API
        - 🛡️ SOA (Safe Operating Area) analysis
        - 🤖 AI-powered circuit analysis
        - 💬 Interactive chat interface
        - 📊 Visual analysis results
        
        **Getting Started:**
        1. Upload your KiCad netlist and BOM files
        2. Optionally upload operating conditions
        3. Click "Load Project" to start analysis
        4. Chat with the AI about your circuit!
        
        **Example Questions:**
        - "Explain the power supply section"
        - "Are there any SOA violations?"
        - "Suggest improvements for this design"
        - "What's the purpose of component R1?"
        """)

def generate_chat_response(prompt, project_data, analysis_results):
    """Generate AI response based on user prompt and project data"""
    # Simple rule-based responses for now
    # In a real implementation, this would use a more sophisticated AI model
    
    prompt_lower = prompt.lower()
    
    if "power" in prompt_lower or "alimentation" in prompt_lower:
        return analyze_power_section(project_data, analysis_results)
    elif "soa" in prompt_lower or "safety" in prompt_lower or "sécurité" in prompt_lower:
        return analyze_soa_section(analysis_results)
    elif "improve" in prompt_lower or "optimize" in prompt_lower or "améliorer" in prompt_lower:
        return suggest_improvements(project_data, analysis_results)
    elif "explain" in prompt_lower or "explique" in prompt_lower:
        return explain_circuit(project_data, analysis_results)
    else:
        return f"I understand you're asking about: '{prompt}'. Based on your circuit analysis, here's what I found:\n\n{analysis_results.get('ai', 'No analysis available yet.')}"

def analyze_power_section(project_data, analysis_results):
    """Analyze power supply section"""
    bom = project_data['bom']
    netlist = project_data['netlist']
    
    # Find power-related components by multiple criteria
    power_components = []
    
    # 1. Components with power-related references (U, Q, D, V, R, C for power)
    power_refs = bom[bom['ref'].str.contains('U|Q|D|V|R|C', na=False)]
    
    # 2. Components with power-related values
    power_values = bom[bom['value'].str.contains('V|A|W|mW|uF|mF|F|k|M|G|T', na=False, case=False)]
    
    # 3. Components with power-related MPNs
    power_mpns = bom[bom['mpn'].str.contains('regulator|converter|transformer|power|supply|voltage|current', na=False, case=False)]
    
    # Combine all power components
    all_power = pd.concat([power_refs, power_values, power_mpns]).drop_duplicates()
    
    # Also check netlist for voltage sources and power components
    voltage_sources = []
    if 'components' in netlist:
        for comp in netlist['components']:
            ref = comp.get('ref', '')
            value = comp.get('value', '')
            comp_type = comp.get('type', '')
            
            # Check for voltage sources (V, I, E, H, F, G)
            if comp_type in ['V', 'I', 'E', 'H', 'F', 'G']:
                voltage_sources.append({
                    'ref': ref,
                    'value': value,
                    'type': comp_type,
                    'mpn': 'SPICE Source'
                })
    
    response = "## Power Supply Analysis\n\n"
    response += f"Found {len(all_power)} power-related components in BOM:\n\n"
    
    if len(all_power) > 0:
        for _, comp in all_power.iterrows():
            response += f"- **{comp['ref']}**: {comp['value']} ({comp.get('mpn', 'N/A')})\n"
    
    if voltage_sources:
        response += f"\nFound {len(voltage_sources)} voltage sources in netlist:\n\n"
        for source in voltage_sources:
            response += f"- **{source['ref']}**: {source['value']} ({source['type']} source)\n"
    
    # Analyze power nets
    power_nets = []
    if 'nets' in netlist:
        for net in netlist['nets']:
            net_name = net.get('name', '')
            if any(keyword in net_name.upper() for keyword in ['VCC', 'VDD', 'VSS', 'GND', 'POWER', 'VIN', 'VOUT', 'VREF', 'VBIAS']):
                power_nets.append(net_name)
    
    if power_nets:
        response += f"\nPower-related nets found: {', '.join(power_nets[:10])}\n"
        if len(power_nets) > 10:
            response += f" (and {len(power_nets) - 10} more...)\n"
    
    if len(all_power) == 0 and len(voltage_sources) == 0:
        response += "\n⚠️ No obvious power supply components detected. This might be a digital-only circuit or the power components are not clearly identified in the netlist.\n"
    
    return response

def analyze_soa_section(analysis_results):
    """Analyze SOA compliance"""
    soa_results = analysis_results.get('soa', {})
    
    response = "## SOA Safety Analysis\n\n"
    
    violations = 0
    warnings = 0
    
    for ref, soa_info in soa_results.items():
        for result in soa_info['compliance']:
            if "❌" in result:
                violations += 1
                response += f"🚨 **{ref}**: {result}\n"
            elif "⚠️" in result:
                warnings += 1
                response += f"⚠️ **{ref}**: {result}\n"
    
    if violations == 0 and warnings == 0:
        response += "✅ All components are within safe operating limits!"
    else:
        response += f"\n**Summary**: {violations} violations, {warnings} warnings\n"
    
    return response

def suggest_improvements(project_data, analysis_results):
    """Suggest design improvements"""
    response = "## Design Improvement Suggestions\n\n"
    
    # Analyze component count
    component_count = len(project_data['bom'])
    if component_count > 50:
        response += "📊 **Complexity**: Your design has many components. Consider modularization.\n\n"
    
    # Check for missing data
    bom = project_data['bom']
    missing_mpn = bom['mpn'].isna().sum()
    if missing_mpn > 0:
        response += f"🔍 **Missing Data**: {missing_mpn} components lack MPN. Add manufacturer part numbers for better analysis.\n\n"
    
    response += "💡 **General Recommendations**:\n"
    response += "- Add decoupling capacitors near ICs\n"
    response += "- Ensure proper ground return paths\n"
    response += "- Consider EMI/EMC requirements\n"
    response += "- Add test points for debugging\n"
    
    return response

def explain_circuit(project_data, analysis_results):
    """Explain the circuit functionality"""
    response = "## Circuit Explanation\n\n"
    
    # Analyze by component types
    bom = project_data['bom']
    
    resistors = bom[bom['ref'].str.startswith('R', na=False)]
    capacitors = bom[bom['ref'].str.startswith('C', na=False)]
    ics = bom[bom['ref'].str.startswith('U', na=False)]
    
    response += f"**Component Breakdown**:\n"
    response += f"- Resistors: {len(resistors)} (likely for biasing, current limiting)\n"
    response += f"- Capacitors: {len(capacitors)} (likely for filtering, decoupling)\n"
    response += f"- ICs: {len(ics)} (main functional blocks)\n\n"
    
    response += "**Likely Functions**:\n"
    if len(ics) > 0:
        response += "- Integrated circuits suggest digital or analog processing\n"
    if len(capacitors) > 3:
        response += "- Multiple capacitors suggest power supply filtering\n"
    if len(resistors) > 5:
        response += "- Many resistors suggest analog signal conditioning\n"
    
    return response

# =========================
# 3D Visualization Functions
# =========================

def create_3d_circuit_visualization(netlist: Dict[str, Any], bom_df: pd.DataFrame):
    """Create 3D visualization of the circuit"""
    components = netlist.get('components', [])
    nets = netlist.get('nets', [])
    
    # Create 3D scatter plot for components
    fig = go.Figure()
    
    # Component positions (simulated PCB layout)
    x_pos = []
    y_pos = []
    z_pos = []
    component_names = []
    component_types = []
    component_values = []
    colors = []
    
    # Generate positions for components
    for i, comp in enumerate(components):
        # Simulate PCB layout with some randomness
        x = (i % 10) * 2 + np.random.uniform(-0.5, 0.5)
        y = (i // 10) * 2 + np.random.uniform(-0.5, 0.5)
        z = 0  # All components on same layer initially
        
        x_pos.append(x)
        y_pos.append(y)
        z_pos.append(z)
        
        ref = comp.get('ref', f'C{i}')
        value = comp.get('value', 'Unknown')
        comp_type = comp.get('type', 'X')
        
        component_names.append(ref)
        component_types.append(comp_type)
        component_values.append(value)
        
        # Color by component type
        color_map = {
            'R': '#FF6B6B',  # Red for resistors
            'C': '#4ECDC4',  # Teal for capacitors
            'L': '#45B7D1',  # Blue for inductors
            'D': '#96CEB4',  # Green for diodes
            'Q': '#FFEAA7',  # Yellow for transistors
            'U': '#DDA0DD',  # Purple for ICs
            'V': '#FFB347',  # Orange for voltage sources
            'I': '#98D8C8',  # Mint for current sources
        }
        colors.append(color_map.get(comp_type, '#95A5A6'))  # Gray for unknown
    
    # Add components as 3D scatter
    fig.add_trace(go.Scatter3d(
        x=x_pos,
        y=y_pos,
        z=z_pos,
        mode='markers+text',
        marker=dict(
            size=8,
            color=colors,
            opacity=0.8,
            line=dict(width=2, color='black')
        ),
        text=component_names,
        textposition="top center",
        name="Components",
        hovertemplate="<b>%{text}</b><br>" +
                     "Type: %{customdata[0]}<br>" +
                     "Value: %{customdata[1]}<br>" +
                     "Position: (%{x:.1f}, %{y:.1f}, %{z:.1f})<br>" +
                     "<extra></extra>",
        customdata=list(zip(component_types, component_values))
    ))
    
    # Add nets as 3D lines (limit to first 20 for performance)
    for net in nets[:20]:
        net_name = net.get('name', '')
        nodes = net.get('nodes', [])
        
        if len(nodes) >= 2:
            # Find component positions for this net
            net_x = []
            net_y = []
            net_z = []
            
            for node in nodes:
                ref = node.get('ref', '')
                # Find component position
                for i, comp_name in enumerate(component_names):
                    if comp_name == ref:
                        net_x.append(x_pos[i])
                        net_y.append(y_pos[i])
                        net_z.append(z_pos[i])
                        break
            
            if len(net_x) >= 2:
                # Add net as line
                fig.add_trace(go.Scatter3d(
                    x=net_x,
                    y=net_y,
                    z=net_z,
                    mode='lines',
                    line=dict(
                        color='rgba(100,100,100,0.5)',
                        width=2
                    ),
                    name=f"Net: {net_name}",
                    showlegend=False,
                    hoverinfo='skip'
                ))
    
    # Update layout
    fig.update_layout(
        title="3D Circuit Visualization",
        scene=dict(
            xaxis_title="X Position (mm)",
            yaxis_title="Y Position (mm)",
            zaxis_title="Z Position (mm)",
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)
            )
        ),
        width=800,
        height=600
    )
    
    return fig

def create_3d_power_analysis(simulation_results: Dict[str, Any]):
    """Create 3D power consumption visualization"""
    if not simulation_results.get('available', False):
        return None
    
    component_counts = simulation_results.get('component_counts', {})
    power_consumption = simulation_results.get('estimated_power_consumption', 0)
    
    # Create 3D bar chart
    fig = go.Figure()
    
    # Prepare data for 3D bars
    x_pos = []
    y_pos = []
    z_pos = []
    values = []
    colors = []
    labels = []
    
    for i, (comp_type, count) in enumerate(component_counts.items()):
        x_pos.append(i % 4)
        y_pos.append(i // 4)
        z_pos.append(0)
        values.append(count)
        labels.append(comp_type)
        
        # Color by component type
        color_map = {
            'R': '#FF6B6B',
            'C': '#4ECDC4',
            'L': '#45B7D1',
            'D': '#96CEB4',
            'Q': '#FFEAA7',
            'U': '#DDA0DD',
            'V': '#FFB347',
        }
        colors.append(color_map.get(comp_type, '#95A5A6'))
    
    # Add 3D bars
    fig.add_trace(go.Scatter3d(
        x=x_pos,
        y=y_pos,
        z=values,
        mode='markers',
        marker=dict(
            size=values,
            sizemode='diameter',
            sizeref=2,
            color=colors,
            opacity=0.8,
            line=dict(width=2, color='black')
        ),
        text=labels,
        textposition="top center",
        name="Component Count",
        hovertemplate="<b>%{text}</b><br>Count: %{z}<br><extra></extra>"
    ))
    
    # Add power consumption as surface
    if power_consumption > 0:
        x_surf = np.linspace(0, 3, 10)
        y_surf = np.linspace(0, 3, 10)
        X, Y = np.meshgrid(x_surf, y_surf)
        Z = np.full_like(X, power_consumption * 10)  # Scale for visibility
        
        fig.add_trace(go.Surface(
            x=X, y=Y, z=Z,
            colorscale='Viridis',
            opacity=0.3,
            name=f"Power: {power_consumption:.2f}W"
        ))
    
    fig.update_layout(
        title="3D Power Analysis",
        scene=dict(
            xaxis_title="Component Type",
            yaxis_title="Category",
            zaxis_title="Count / Power",
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)
            )
        ),
        width=800,
        height=600
    )
    
    return fig

def create_3d_soa_visualization(soa_results: Dict[str, Any]):
    """Create 3D SOA safety visualization"""
    if not soa_results:
        return None
    
    fig = go.Figure()
    
    # Prepare SOA data
    x_vals = []
    y_vals = []
    z_vals = []
    colors = []
    labels = []
    
    for ref, soa_info in soa_results.items():
        soa_data = soa_info.get('soa_data', {})
        compliance = soa_info.get('compliance', [])
        
        if soa_data:
            # Extract SOA parameters
            vds_max = soa_data.get('Vds_max', 0)
            id_max = soa_data.get('Id_max', 0)
            pd_max = soa_data.get('Pd_max', 0)
            
            x_vals.append(vds_max)
            y_vals.append(id_max)
            z_vals.append(pd_max)
            labels.append(ref)
            
            # Color by compliance status
            if any("❌" in str(c) for c in compliance):
                colors.append('#FF6B6B')  # Red for violations
            elif any("⚠️" in str(c) for c in compliance):
                colors.append('#FFEAA7')  # Yellow for warnings
            else:
                colors.append('#96CEB4')  # Green for OK
    
    if x_vals:
        fig.add_trace(go.Scatter3d(
            x=x_vals,
            y=y_vals,
            z=z_vals,
            mode='markers+text',
            marker=dict(
                size=10,
                color=colors,
                opacity=0.8,
                line=dict(width=2, color='black')
            ),
            text=labels,
            textposition="top center",
            name="SOA Analysis",
            hovertemplate="<b>%{text}</b><br>" +
                         "Vds_max: %{x:.1f}V<br>" +
                         "Id_max: %{y:.1f}A<br>" +
                         "Pd_max: %{z:.1f}W<br>" +
                         "<extra></extra>"
        ))
    
    fig.update_layout(
        title="3D SOA Safety Analysis",
        scene=dict(
            xaxis_title="Vds_max (V)",
            yaxis_title="Id_max (A)",
            zaxis_title="Pd_max (W)",
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)
            )
        ),
        width=800,
        height=600
    )
    
    return fig

if __name__ == "__main__":
    chat_interface()
