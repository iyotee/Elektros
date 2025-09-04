#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script to check file parsing
"""

import os
from kicad_ai_allinone import read_netlist, read_bom, load_operating_conditions

def test_example_files():
    """Test parsing of example files"""
    print("🧪 Testing example files...")
    
    # Test netlist
    netlist_path = "examples/sample_netlist.xml"
    if os.path.exists(netlist_path):
        print(f"✅ Testing netlist: {netlist_path}")
        try:
            netlist = read_netlist(netlist_path)
            print(f"  ✅ Netlist loaded: {len(netlist.get('components', []))} components")
        except Exception as e:
            print(f"  ❌ Netlist error: {e}")
    else:
        print(f"❌ Netlist file not found: {netlist_path}")
    
    # Test BOM
    bom_path = "examples/sample_bom.csv"
    if os.path.exists(bom_path):
        print(f"✅ Testing BOM: {bom_path}")
        try:
            bom = read_bom(bom_path)
            print(f"  ✅ BOM loaded: {len(bom)} items")
        except Exception as e:
            print(f"  ❌ BOM error: {e}")
    else:
        print(f"❌ BOM file not found: {bom_path}")
    
    # Test operating conditions
    operating_path = "examples/operating_conditions.yaml"
    if os.path.exists(operating_path):
        print(f"✅ Testing operating conditions: {operating_path}")
        try:
            operating = load_operating_conditions(operating_path)
            print(f"  ✅ Operating conditions loaded: {len(operating)} components")
        except Exception as e:
            print(f"  ❌ Operating conditions error: {e}")
    else:
        print(f"❌ Operating conditions file not found: {operating_path}")

if __name__ == "__main__":
    test_example_files()
