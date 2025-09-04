#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nexar/Octopart API client with provided credentials
"""

import requests
import json
from typing import Optional, Tuple, Dict, Any, List
import time


class NexarClient:
    """Client for Nexar/Octopart API with provided credentials"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.nexar.com"
        self.graphql_url = f"{self.base_url}/graphql"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
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
            # GraphQL query for part search
            query = """
            query PartSearch($mpn: String!) {
              supSearch(
                q: $mpn
                inStockOnly: false
                limit: 1
              ) {
                results {
                  part {
                    mpn
                    manufacturer {
                      name
                    }
                    shortDescription
                    specs {
                      attribute {
                        name
                      }
                      value {
                        text
                      }
                    }
                    medianPrice1000 {
                      price
                      currency
                    }
                    category {
                      name
                    }
                    documents {
                      url
                      name
                      type
                    }
                    cadModels {
                      url
                      name
                      type
                    }
                  }
                }
              }
            }
            """
            
            variables = {"mpn": mpn}
            
            response = requests.post(
                self.graphql_url,
                json={"query": query, "variables": variables},
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "errors" in data:
                    print(f"[WARN] Nexar API error for {mpn}: {data['errors']}")
                    return None, None
                
                results = data.get("data", {}).get("supSearch", {}).get("results", [])
                
                if not results:
                    return None, None
                
                part = results[0]["part"]
                
                # Extract datasheet URL
                datasheet_url = None
                documents = part.get("documents", [])
                for doc in documents:
                    if doc.get("type") in ["datasheet", "data sheet", "specification"]:
                        datasheet_url = doc.get("url")
                        break
                
                # Extract SPICE model URL
                spice_url = None
                cad_models = part.get("cadModels", [])
                for model in cad_models:
                    model_type = model.get("type", "").lower()
                    if any(keyword in model_type for keyword in ["spice", "pspice", "ltspice", "simulation"]):
                        spice_url = model.get("url")
                        break
                
                return datasheet_url, spice_url
            else:
                print(f"[WARN] Nexar API HTTP error {response.status_code} for {mpn}")
                return None, None
                
        except Exception as e:
            print(f"[WARN] Nexar API request failed for {mpn}: {e}")
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
            query = """
            query PartDetails($mpn: String!) {
              supSearch(
                q: $mpn
                inStockOnly: false
                limit: 1
              ) {
                results {
                  part {
                    mpn
                    manufacturer {
                      name
                    }
                    shortDescription
                    longDescription
                    specs {
                      attribute {
                        name
                      }
                      value {
                        text
                      }
                    }
                    medianPrice1000 {
                      price
                      currency
                    }
                    category {
                      name
                    }
                    documents {
                      url
                      name
                      type
                    }
                    cadModels {
                      url
                      name
                      type
                    }
                    sellers {
                      company {
                        name
                      }
                      offers {
                        clickUrl
                        inventoryLevel
                        prices {
                          price
                          currency
                          quantity
                        }
                      }
                    }
                  }
                }
              }
            }
            """
            
            variables = {"mpn": mpn}
            
            response = requests.post(
                self.graphql_url,
                json={"query": query, "variables": variables},
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "errors" in data:
                    print(f"[WARN] Nexar API error for {mpn}: {data['errors']}")
                    return None
                
                results = data.get("data", {}).get("supSearch", {}).get("results", [])
                
                if not results:
                    return None
                
                return results[0]["part"]
            else:
                print(f"[WARN] Nexar API HTTP error {response.status_code} for {mpn}")
                return None
                
        except Exception as e:
            print(f"[WARN] Nexar API request failed for {mpn}: {e}")
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
    
    def get_manufacturer_parts(self, manufacturer: str, category: str = None) -> List[Dict[str, Any]]:
        """
        Search for parts by manufacturer and category
        
        Args:
            manufacturer: Manufacturer name
            category: Optional category filter
            
        Returns:
            List of part dictionaries
        """
        try:
            query = """
            query ManufacturerParts($manufacturer: String!, $category: String) {
              supSearch(
                q: $manufacturer
                inStockOnly: false
                limit: 50
              ) {
                results {
                  part {
                    mpn
                    manufacturer {
                      name
                    }
                    shortDescription
                    category {
                      name
                    }
                    medianPrice1000 {
                      price
                      currency
                    }
                  }
                }
              }
            }
            """
            
            variables = {
                "manufacturer": manufacturer,
                "category": category
            }
            
            response = requests.post(
                self.graphql_url,
                json={"query": query, "variables": variables},
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "errors" in data:
                    print(f"[WARN] Nexar API error: {data['errors']}")
                    return []
                
                results = data.get("data", {}).get("supSearch", {}).get("results", [])
                
                # Filter by category if specified
                if category:
                    results = [
                        r for r in results 
                        if r["part"].get("category", {}).get("name", "").lower() == category.lower()
                    ]
                
                return [r["part"] for r in results]
            else:
                print(f"[WARN] Nexar API HTTP error {response.status_code}")
                return []
                
        except Exception as e:
            print(f"[WARN] Nexar API request failed: {e}")
            return []
    
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
            print(f"[WARN] Nexar API connection test failed: {e}")
            return False


# Update the APIManager to use NexarClient
def create_nexar_api_manager():
    """Create API manager with Nexar credentials"""
    nexar_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjA5NzI5QTkyRDU0RDlERjIyRDQzMENBMjNDNkI4QjJFIiwidHlwIjoiYXQrand0In0.eyJuYmYiOjE3NTY5ODU4NjUsImV4cCI6MTc1NzA3MjI2NSwiaXNzIjoiaHR0cHM6Ly9pZGVudGl0eS5uZXhhci5jb20iLCJjbGllbnRfaWQiOiIxODEwYjk4ZC02NTYyLTQ5ZDgtOTNkMy0yMjM5NzFiZjZjZGMiLCJzdWIiOiJFNTIzREVBNy1BODU2LTRFRTUtQjM0Ny03RUI3OEE3N0E0NEUiLCJhdXRoX3RpbWUiOjE3NTY5ODU2OTAsImlkcCI6Ikdvb2dsZSIsInByaXZhdGVfY2xhaW1zX2lkIjoiZjhjNTcxYzctMDM1Mi00YjFkLWI5ZjYtYjQ1NTFiOGI3MjcwIiwicHJpdmF0ZV9jbGFpbXNfc2VjcmV0IjoibnNnNytsZG5RZ2tIMDlpcnJGN2xxQzVzb3RncEx5MVVTaGdOaWhOVktoWT0iLCJqdGkiOiI2NTdFMDFGRjU2NjUxRUY4M0YyNjVCRkE4NTYxOTI4NyIsInNpZCI6IjczRjNGRDBBNjFEQjk3MzRCNzQ1REQyN0VBMEY1NzNDIiwiaWF0IjoxNzU2OTg1ODY1LCJzY29wZSI6WyJvcGVuaWQiLCJ1c2VyLmFjY2VzcyIsInByb2ZpbGUiLCJlbWFpbCIsInVzZXIuZGV0YWlscyIsImRlc2lnbi5kb21haW4iLCJzdXBwbHkuZG9tYWluIl0sImFtciI6WyJleHRlcm5hbCJdfQ.eqCuD2fTetsg7yXAESGQEah5vONruj4zBlB_Vb0jAroIjl14bdpwRzWrC8nzdl7SkMSr8nPp3tGaO6hacuPGCSPdbS5vRoBMZM_Yh8b4m70IAzeDUevZiqtdGMSsIlvw4TzGZ6LLTr60cHg8hPPAuYr4h7j5gYr1axbycFvBU-2hQ2Sr09AnF_g_gKyLmNjOrfx_8UMIK5U5Y18goBKZvr-dWQPkK-MVy0deLAraj2GI6SqWCX9NHk2sLG5sSWhNLHecJl-WuNSjJexqpWfiArH7XwcU3nFaBCxxIJGrHs3ARhszeCbwc84pA5GFo3iM_PCW8JAdI9sPmj6aK6BdQQ"
    
    return NexarClient(nexar_token)
