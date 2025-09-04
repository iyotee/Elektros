#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Streamlit Cloud Entry Point
This file is the main entry point for Streamlit Cloud deployment
"""

import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and run the main app
from app import chat_interface

if __name__ == "__main__":
    chat_interface()
