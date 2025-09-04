#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SOA (Safe Operating Area) extraction from datasheets
"""

import re
import pdfplumber
from typing import Dict, List, Optional, Tuple
import os


class SOAPattern:
    """Represents a SOA pattern for extraction"""
    
    def __init__(self, name: str, pattern: str, unit: str, description: str = ""):
        self.name = name
        self.pattern = pattern
        self.unit = unit
        self.description = description
    
    def extract(self, text: str) -> Optional[float]:
        """Extract value from text using the pattern"""
        match = re.search(self.pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, IndexError):
                return None
        return None


class SOAExtractor:
    """Extracts SOA parameters from PDF datasheets"""
    
    def __init__(self):
        self.patterns = [
            SOAPattern(
                "Vds_max",
                r"(?:Vds|Drain[-\s]?Source\s*Voltage)[^\n]*?(\d+\.?\d*)\s*V",
                "V",
                "Maximum drain-source voltage"
            ),
            SOAPattern(
                "Id_max",
                r"(?:Id|Drain\s*Current)[^\n]*?(\d+\.?\d*)\s*A",
                "A",
                "Maximum drain current"
            ),
            SOAPattern(
                "Pd_max",
                r"(?:P[dD]|Power\s*Dissipation)[^\n]*?(\d+\.?\d*)\s*W",
                "W",
                "Maximum power dissipation"
            ),
            SOAPattern(
                "Vr_max",
                r"(?:Vr|Reverse\s*Voltage)[^\n]*?(\d+\.?\d*)\s*V",
                "V",
                "Maximum reverse voltage"
            ),
            SOAPattern(
                "If_max",
                r"(?:If|Forward\s*Current)[^\n]*?(\d+\.?\d*)\s*A",
                "A",
                "Maximum forward current"
            ),
            SOAPattern(
                "Vce_max",
                r"(?:Vce|Collector[-\s]?Emitter\s*Voltage)[^\n]*?(\d+\.?\d*)\s*V",
                "V",
                "Maximum collector-emitter voltage"
            ),
            SOAPattern(
                "Ic_max",
                r"(?:Ic|Collector\s*Current)[^\n]*?(\d+\.?\d*)\s*A",
                "A",
                "Maximum collector current"
            ),
            SOAPattern(
                "Vbe_max",
                r"(?:Vbe|Base[-\s]?Emitter\s*Voltage)[^\n]*?(\d+\.?\d*)\s*V",
                "V",
                "Maximum base-emitter voltage"
            ),
            SOAPattern(
                "Ib_max",
                r"(?:Ib|Base\s*Current)[^\n]*?(\d+\.?\d*)\s*A",
                "A",
                "Maximum base current"
            ),
        ]
        
        # Keywords that indicate SOA sections
        self.soa_keywords = [
            "Absolute Maximum Ratings",
            "Safe Operating Area",
            "Maximum Ratings",
            "Electrical Characteristics",
            "Limiting Values",
            "Absolute Maximum",
            "Maximum Operating",
            "Peak Ratings"
        ]
    
    def extract_from_pdf(self, pdf_path: str) -> Dict[str, float]:
        """
        Extract SOA parameters from a PDF file
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary of extracted SOA parameters
        """
        if not pdf_path or not os.path.exists(pdf_path):
            return {}
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Prioritize pages with SOA-related keywords
                prioritized_pages = []
                other_pages = []
                
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    if any(keyword in text for keyword in self.soa_keywords):
                        prioritized_pages.append(text)
                    else:
                        other_pages.append(text)
                
                # Extract from prioritized pages first
                all_pages = prioritized_pages + other_pages
                return self._extract_from_texts(all_pages)
                
        except Exception as e:
            print(f"[WARN] SOA extraction failed for {pdf_path}: {e}")
            return {}
    
    def _extract_from_texts(self, texts: List[str]) -> Dict[str, float]:
        """Extract SOA parameters from a list of text strings"""
        results = {}
        
        for text in texts:
            for pattern in self.patterns:
                if pattern.name in results:
                    continue  # Already found this parameter
                    
                value = pattern.extract(text)
                if value is not None:
                    results[pattern.name] = value
                    
            # Stop if we have enough parameters
            if len(results) >= 5:
                break
                
        return results
    
    def extract_from_text(self, text: str) -> Dict[str, float]:
        """
        Extract SOA parameters from text
        
        Args:
            text: Text to extract from
            
        Returns:
            Dictionary of extracted SOA parameters
        """
        return self._extract_from_texts([text])
    
    def validate_soa(self, soa: Dict[str, float]) -> List[str]:
        """
        Validate extracted SOA parameters for reasonableness
        
        Args:
            soa: Dictionary of SOA parameters
            
        Returns:
            List of validation warnings
        """
        warnings = []
        
        # Check for reasonable voltage ranges
        voltage_params = ["Vds_max", "Vr_max", "Vce_max", "Vbe_max"]
        for param in voltage_params:
            if param in soa:
                value = soa[param]
                if value < 0:
                    warnings.append(f"Negative voltage for {param}: {value}V")
                elif value > 1000:
                    warnings.append(f"Very high voltage for {param}: {value}V")
        
        # Check for reasonable current ranges
        current_params = ["Id_max", "If_max", "Ic_max", "Ib_max"]
        for param in current_params:
            if param in soa:
                value = soa[param]
                if value < 0:
                    warnings.append(f"Negative current for {param}: {value}A")
                elif value > 100:
                    warnings.append(f"Very high current for {param}: {value}A")
        
        # Check for reasonable power ranges
        if "Pd_max" in soa:
            value = soa["Pd_max"]
            if value < 0:
                warnings.append(f"Negative power for Pd_max: {value}W")
            elif value > 1000:
                warnings.append(f"Very high power for Pd_max: {value}W")
        
        return warnings


class SOAChecker:
    """Checks SOA compliance against operating conditions"""
    
    def __init__(self, safety_margin: float = 0.8):
        self.safety_margin = safety_margin
    
    def check_compliance(self, soa: Dict[str, float], operating_conditions: Dict[str, float]) -> List[str]:
        """
        Check SOA compliance against operating conditions
        
        Args:
            soa: SOA limits from datasheet
            operating_conditions: Actual operating conditions
            
        Returns:
            List of compliance check results
        """
        results = []
        
        if not soa or not operating_conditions:
            return ["No SOA data or operating conditions available"]
        
        # Define parameter pairs to check
        checks = [
            ("Vds", "Vds_max", "V"),
            ("Id", "Id_max", "A"),
            ("Pd", "Pd_max", "W"),
            ("Vr", "Vr_max", "V"),
            ("If", "If_max", "A"),
            ("Vce", "Vce_max", "V"),
            ("Ic", "Ic_max", "A"),
            ("Vbe", "Vbe_max", "V"),
            ("Ib", "Ib_max", "A"),
        ]
        
        for param, limit_param, unit in checks:
            if param in operating_conditions and limit_param in soa:
                actual = operating_conditions[param]
                limit = soa[limit_param]
                
                if actual > limit:
                    results.append(f"❌ {param}={actual}{unit} > {limit}{unit} (limit exceeded)")
                elif actual > self.safety_margin * limit:
                    results.append(f"⚠️ {param}={actual}{unit} close to limit {limit}{unit} (safety margin)")
                else:
                    results.append(f"✅ {param}={actual}{unit} OK (limit {limit}{unit})")
        
        return results
