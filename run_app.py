#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple launcher for KiCad AI Interactive Chat
"""

import subprocess
import sys
import os
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'streamlit',
        'pandas',
        'plotly',
        'requests',
        'pdfplumber',
        'yaml'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        
        try:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install'
            ] + missing_packages, check=True)
            print("✅ Dependencies installed successfully!")
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            return False
    
    return True

def launch_app():
    """Launch the Streamlit app"""
    app_path = Path(__file__).parent / "app.py"
    
    if not app_path.exists():
        print(f"❌ App file not found: {app_path}")
        return False
    
    print("🚀 Launching KiCad AI Interactive Chat...")
    print("The app will open in your default web browser")
    print("Press Ctrl+C to stop the application")
    print("-" * 50)
    
    try:
        # Launch Streamlit app
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', str(app_path),
            '--server.port', '8501',
            '--server.address', 'localhost',
            '--browser.gatherUsageStats', 'false'
        ])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error launching app: {e}")
        return False
    
    return True

def main():
    """Main launcher function"""
    print("🔌 KiCad AI Interactive Chat Launcher")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Dependency check failed")
        return 1
    
    # Launch app
    if not launch_app():
        print("❌ Failed to launch application")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
