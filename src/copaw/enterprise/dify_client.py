import httpx
from typing import Dict, Any, Optional

class DifyClient:
    """Client for interacting with Dify API"""
    
    def __init__(self, api_url: str, api_key: str):
        # Ensure url does not have trailing slash
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    async def run_workflow(self, inputs: Dict[str, Any], user: str, response_mode: str = "blocking") -> Dict[str, Any]:
        """
        Run a Dify Workflow app.
        
        Args:
            inputs: Dictionary containing workflow input variables.
            user: Identifier of the end user.
            response_mode: 'blocking' or 'streaming'. Streaming returns events, blocking returns final result.
            
        Returns:
            Dictionary with execution results or streaming event response.
        """
        url = f"{self.api_url}/workflows/run"
        payload = {
            "inputs": inputs,
            "response_mode": response_mode,
            "user": user
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self.headers, timeout=60.0)
            response.raise_for_status()
            return response.json()
            
    async def get_workflow_status(self, task_id: str, user: str) -> Dict[str, Any]:
        """
        Get the status of a specific workflow execution.
        """
        url = f"{self.api_url}/workflows/run/{task_id}"
        params = {"user": user}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=self.headers, timeout=10.0)
            response.raise_for_status()
            return response.json()

    async def get_app_parameters(self, user: str) -> Dict[str, Any]:
        """
        Get application parameters (input definitions) configured in Dify.
        """
        url = f"{self.api_url}/parameters"
        params = {"user": user}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=self.headers, timeout=10.0)
            response.raise_for_status()
            return response.json()
