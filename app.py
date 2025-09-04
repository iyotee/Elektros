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
from datetime import datetime
import base64

# Import our modules
from utils.api_clients import APIManager
from utils.soa_extractor import SOAExtractor, SOAChecker
from utils.spice_simulator import BodeAnalyzer
from utils.ai_analyzer import AIAnalyzer, ReportGenerator
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
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
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
        with tempfile.TemporaryDirectory() as temp_dir:
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
    
    for _, row in bom_df.iterrows():
        ref = str(row.get('ref', '')).strip()
        if not ref:
            continue
            
        # Extract SOA from datasheet if available
        datasheet_path = row.get('datasheet_path', '')
        soa_data = {}
        if datasheet_path and os.path.exists(datasheet_path):
            soa_data = soa_extractor.extract_from_pdf(datasheet_path)
        
        # Check compliance
        component_conditions = operating_conditions.get(ref, {})
        compliance_results = soa_checker.check_compliance(soa_data, component_conditions)
        
        soa_results[ref] = {
            'soa_data': soa_data,
            'operating_conditions': component_conditions,
            'compliance': compliance_results
        }
    
    return soa_results

def run_ai_analysis(project_data, bode_data=None):
    """Run AI analysis on the project"""
    ai_analyzer = AIAnalyzer("google/flan-t5-large", "cpu")
    
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
                st.write(f"- Datasheet: [Link]({component_data['datasheet']})")
        
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
    st.markdown('<h1 class="main-header">🔌 KiCad AI Interactive Chat</h1>', unsafe_allow_html=True)
    
    # Sidebar for file uploads
    with st.sidebar:
        st.header("📁 Project Files")
        
        # File uploaders
        netlist_file = st.file_uploader(
            "Upload Netlist (.net/.xml)",
            type=['net', 'xml'],
            help="Upload your KiCad netlist file"
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
                            st.session_state.project_data['bom'] = enriched_bom
                        
                        # Analyze SOA
                        with st.spinner("Analyzing SOA compliance..."):
                            soa_results = analyze_soa(enriched_bom, project_data['operating_conditions'])
                            st.session_state.analysis_results['soa'] = soa_results
                        
                        # Run AI analysis
                        with st.spinner("Running AI analysis..."):
                            ai_analysis = run_ai_analysis(project_data)
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
        tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "🔧 Components", "📊 Analysis", "📄 Report"])
        
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
            # Full report
            st.subheader("📄 Full Report")
            
            if 'ai' in st.session_state.analysis_results:
                report_generator = ReportGenerator()
                full_report = report_generator.generate_report(
                    project_data['project_name'],
                    project_data['bom'],
                    project_data['netlist'],
                    project_data['operating_conditions'],
                    None,  # bode_data
                    st.session_state.analysis_results['ai']
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
    power_components = bom[bom['ref'].str.contains('U|Q|D', na=False)]
    
    response = "## Power Supply Analysis\n\n"
    response += f"Found {len(power_components)} power-related components:\n\n"
    
    for _, comp in power_components.iterrows():
        response += f"- **{comp['ref']}**: {comp['value']} ({comp['mpn']})\n"
    
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

if __name__ == "__main__":
    chat_interface()
