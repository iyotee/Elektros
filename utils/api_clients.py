#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API clients for Octopart and Mouser
"""

import requests
from typing import Optional, Tuple, Dict, Any, List
import json


class OctopartClient:
    """Client for Octopart API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://octopart.com/api/v4"
        self.graphql_url = f"{self.base_url}/graph"
    
    def search_part(self, mpn: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Search for a part by MPN and return datasheet URL and SPICE model URL
        
        Args:
            mpn: Manufacturer Part Number
            
        Returns:
            Tuple of (datasheet_url, spice_model_url)
        """
        if not self.api_key or not mpn:
            return None, None
            
        # Try GraphQL API first
        try:
            return self._search_graphql(mpn)
        except Exception as e:
            print(f"[WARN] Octopart GraphQL failed for {mpn}: {e}")
            
        # Fallback to REST API
        try:
            return self._search_rest(mpn)
        except Exception as e:
            print(f"[WARN] Octopart REST failed for {mpn}: {e}")
            
        return None, None
    
    def _search_graphql(self, mpn: str) -> Tuple[Optional[str], Optional[str]]:
        """Search using GraphQL API"""
        query = """
        query ($mpn: String!) {
          parts(mpn: $mpn) {
            datasheets { 
              url 
              name
            }
            models { 
              url 
              type 
              name
            }
            specs {
              attribute {
                name
              }
              value {
                text
              }
            }
          }
        }
        """
        
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": self.api_key
        }
        
        payload = {
            "query": query,
            "variables": {"mpn": mpn}
        }
        
        response = requests.post(
            self.graphql_url, 
            json=payload, 
            headers=headers, 
            timeout=15
        )
        response.raise_for_status()
        
        data = response.json()
        parts = data.get("data", {}).get("parts", [])
        
        if not parts:
            return None, None
            
        part = parts[0]
        
        # Get datasheet URL
        datasheet_url = None
        datasheets = part.get("datasheets", [])
        if datasheets:
            datasheet_url = datasheets[0].get("url")
        
        # Get SPICE model URL
        spice_url = None
        models = part.get("models", [])
        for model in models:
            model_type = model.get("type", "").lower()
            if any(keyword in model_type for keyword in ["spice", "pspice", "ltspice"]):
                spice_url = model.get("url")
                break
        
        return datasheet_url, spice_url
    
    def _search_rest(self, mpn: str) -> Tuple[Optional[str], Optional[str]]:
        """Search using REST API (placeholder)"""
        # This is a placeholder - actual REST API implementation would go here
        # The real Octopart REST API has different endpoints and authentication
        return None, None
    
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            query = """
            query TestConnection {
              supSearch(
                q: "test"
                limit: 1
              ) {
                results {
                  part {
                    mpn
                  }
                }
              }
            }
            """
            
            response = requests.post(
                self.graphql_url,
                json={"query": query},
                headers=self.headers,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"[WARN] Octopart API connection test failed: {e}")
            return False


class MouserClient:
    """Client for Mouser API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api.mouser.com/api/v1"
    
    def search_part(self, mpn: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Search for a part by MPN and return datasheet URL
        
        Args:
            mpn: Manufacturer Part Number
            
        Returns:
            Tuple of (datasheet_url, spice_model_url)
        """
        if not self.api_key or not mpn:
            return None, None
            
        try:
            url = f"{self.base_url}/search/partnumber"
            headers = {"Content-Type": "application/json"}
            payload = {
                "SearchByPartRequest": {
                    "mouserPartNumber": mpn,
                    "apiKey": self.api_key
                }
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            search_results = data.get("SearchResults", {})
            parts = search_results.get("Parts", [])
            
            if not parts:
                return None, None
                
            part = parts[0]
            datasheet_url = part.get("DataSheetUrl")
            
            # Mouser typically doesn't provide SPICE models directly
            return datasheet_url, None
            
        except Exception as e:
            print(f"[WARN] Mouser search failed for {mpn}: {e}")
            return None, None


class APIManager:
    """Manages multiple API clients"""
    
    def __init__(self, octopart_key: Optional[str] = None, mouser_key: Optional[str] = None):
        self.octopart = OctopartClient(octopart_key) if octopart_key else None
        self.mouser = MouserClient(mouser_key) if mouser_key else None
    
    def search_part(self, mpn: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Search for a part using available APIs
        
        Args:
            mpn: Manufacturer Part Number
            
        Returns:
            Tuple of (datasheet_url, spice_model_url)
        """
        datasheet_url = None
        spice_url = None
        
        # Try Octopart first
        if self.octopart:
            ds, sp = self.octopart.search_part(mpn)
            datasheet_url = ds
            spice_url = sp
        
        # Try Mouser if no datasheet found
        if not datasheet_url and self.mouser:
            ds, _ = self.mouser.search_part(mpn)
            datasheet_url = ds
        
        return datasheet_url, spice_url
    
    def get_part_details(self, mpn: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed part information from available APIs
        
        Args:
            mpn: Manufacturer Part Number
            
        Returns:
            Dictionary with part details
        """
        # Try Octopart first
        if self.octopart:
            details = self.octopart.get_part_details(mpn)
            if details:
                return details
        
        # Try Mouser if no details found
        if self.mouser:
            details = self.mouser.get_part_details(mpn)
            if details:
                return details
        
        return None
    
    def search_parts_batch(self, mpns: List[str]) -> Dict[str, Tuple[Optional[str], Optional[str]]]:
        """
        Search for multiple parts using available APIs
        
        Args:
            mpns: List of Manufacturer Part Numbers
            
        Returns:
            Dictionary mapping MPN to (datasheet_url, spice_model_url)
        """
        results = {}
        
        # Use Octopart for batch search if available
        if self.octopart:
            results = self.octopart.search_parts_batch(mpns)
        
        # Fill in missing results with Mouser
        if self.mouser:
            missing_mpns = [mpn for mpn in mpns if mpn not in results or not results[mpn][0]]
            mouser_results = self.mouser.search_parts_batch(missing_mpns)
            
            for mpn, (ds_url, sp_url) in mouser_results.items():
                if mpn not in results or not results[mpn][0]:
                    results[mpn] = (ds_url, sp_url)
        
        return results
    
    def test_connections(self) -> Dict[str, bool]:
        """
        Test all API connections
        
        Returns:
            Dictionary with connection status for each API
        """
        results = {}
        
        if self.octopart:
            results["octopart"] = self.octopart.test_connection()
        
        if self.mouser:
            results["mouser"] = self.mouser.test_connection()
        
        return results
