#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mouser API client with provided credentials
"""

import requests
import json
from typing import Optional, Tuple, Dict, Any, List
import time


class MouserClient:
    """Client for Mouser API with provided credentials"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.mouser.com/api/v1"
        self.headers = {
            "Content-Type": "application/json"
        }
    
    def search_part(self, mpn: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Search for a part by MPN and return datasheet URL and SPICE model URL
        
        Args:
            mpn: Manufacturer Part Number
            
        Returns:
            Tuple of (datasheet_url, spice_model_url)
        """
        if not mpn:
            return None, None
        
        try:
            url = f"{self.base_url}/search/partnumber"
            payload = {
                "SearchByPartRequest": {
                    "mouserPartNumber": mpn,
                    "apiKey": self.api_key
                }
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                search_results = data.get("SearchResults", {})
                parts = search_results.get("Parts", [])
                
                if not parts:
                    return None, None
                
                part = parts[0]
                
                # Extract datasheet URL
                datasheet_url = part.get("DataSheetUrl")
                
                # Mouser doesn't typically provide SPICE models directly
                spice_url = None
                
                return datasheet_url, spice_url
            else:
                print(f"[WARN] Mouser API HTTP error {response.status_code} for {mpn}")
                return None, None
                
        except Exception as e:
            print(f"[WARN] Mouser API request failed for {mpn}: {e}")
            return None, None
    
    def get_part_details(self, mpn: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed part information
        
        Args:
            mpn: Manufacturer Part Number
            
        Returns:
            Dictionary with part details
        """
        if not mpn:
            return None
        
        try:
            url = f"{self.base_url}/search/partnumber"
            payload = {
                "SearchByPartRequest": {
                    "mouserPartNumber": mpn,
                    "apiKey": self.api_key
                }
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                search_results = data.get("SearchResults", {})
                parts = search_results.get("Parts", [])
                
                if not parts:
                    return None
                
                part = parts[0]
                
                # Extract detailed information
                part_details = {
                    "mpn": part.get("MfrPartNumber"),
                    "manufacturer": part.get("Manufacturer"),
                    "description": part.get("Description"),
                    "datasheet_url": part.get("DataSheetUrl"),
                    "category": part.get("Category"),
                    "lifecycle": part.get("LifecycleStatus"),
                    "rohs_status": part.get("ROHSStatus"),
                    "pricing": part.get("PriceBreaks", []),
                    "availability": part.get("Availability", {}),
                    "specifications": part.get("ProductAttributes", []),
                    "mouser_part_number": part.get("MouserPartNumber"),
                    "mouser_url": part.get("ProductDetailUrl")
                }
                
                return part_details
            else:
                print(f"[WARN] Mouser API HTTP error {response.status_code} for {mpn}")
                return None
                
        except Exception as e:
            print(f"[WARN] Mouser API request failed for {mpn}: {e}")
            return None
    
    def search_parts_batch(self, mpns: List[str]) -> Dict[str, Tuple[Optional[str], Optional[str]]]:
        """
        Search for multiple parts in batch
        
        Args:
            mpns: List of Manufacturer Part Numbers
            
        Returns:
            Dictionary mapping MPN to (datasheet_url, spice_model_url)
        """
        results = {}
        
        for mpn in mpns:
            if mpn:
                datasheet_url, spice_url = self.search_part(mpn)
                results[mpn] = (datasheet_url, spice_url)
                # Small delay to avoid rate limiting
                time.sleep(0.1)
        
        return results
    
    def search_by_manufacturer(self, manufacturer: str, category: str = None) -> List[Dict[str, Any]]:
        """
        Search for parts by manufacturer and category
        
        Args:
            manufacturer: Manufacturer name
            category: Optional category filter
            
        Returns:
            List of part dictionaries
        """
        try:
            url = f"{self.base_url}/search/keyword"
            payload = {
                "SearchByKeywordRequest": {
                    "keyword": manufacturer,
                    "apiKey": self.api_key,
                    "records": 50
                }
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                search_results = data.get("SearchResults", {})
                parts = search_results.get("Parts", [])
                
                # Filter by category if specified
                if category:
                    parts = [
                        p for p in parts 
                        if p.get("Category", "").lower() == category.lower()
                    ]
                
                # Extract relevant information
                part_list = []
                for part in parts:
                    part_info = {
                        "mpn": part.get("MfrPartNumber"),
                        "manufacturer": part.get("Manufacturer"),
                        "description": part.get("Description"),
                        "datasheet_url": part.get("DataSheetUrl"),
                        "category": part.get("Category"),
                        "mouser_part_number": part.get("MouserPartNumber"),
                        "mouser_url": part.get("ProductDetailUrl")
                    }
                    part_list.append(part_info)
                
                return part_list
            else:
                print(f"[WARN] Mouser API HTTP error {response.status_code}")
                return []
                
        except Exception as e:
            print(f"[WARN] Mouser API request failed: {e}")
            return []
    
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            url = f"{self.base_url}/search/partnumber"
            payload = {
                "SearchByPartRequest": {
                    "mouserPartNumber": "test",
                    "apiKey": self.api_key
                }
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=10
            )
            
            # Even if no results, a 200 response means the API is working
            return response.status_code == 200
            
        except Exception as e:
            print(f"[WARN] Mouser API connection test failed: {e}")
            return False


# Create Mouser client with provided API key
def create_mouser_client():
    """Create Mouser client with provided API key"""
    api_key = "7b994823-8625-4774-a4c6-bb16b95cc7e5"
    return MouserClient(api_key)
