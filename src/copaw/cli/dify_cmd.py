import click
import json
import httpx
from rich.console import Console

from ..config.utils import read_last_api

console = Console()

@click.group(name="dify")
def dify_group():
    """Manage and trigger Dify Enterprise workflows."""
    pass

@dify_group.command(name="run")
@click.option("--connector", required=True, help="Dify connector ID to use")
@click.option("--inputs", required=True, help="JSON string of inputs for the workflow")
@click.option("--user", required=True, default="copaw-cli-user", help="User identifier for Dify execution")
@click.pass_context
def run_workflow(ctx: click.Context, connector: str, inputs: str, user: str):
    """Run a specific Dify workflow securely via the CoPaw API."""
    host = ctx.obj.get("host", "127.0.0.1")
    port = ctx.obj.get("port", 8088)
    base_url = f"http://{host}:{port}/api/enterprise/dify"

    try:
        parsed_inputs = json.loads(inputs)
    except json.JSONDecodeError:
        console.print("[bold red]Error: --inputs must be a valid JSON string.[/bold red]")
        return

    payload = {
        "connector_id": connector,
        "inputs": parsed_inputs,
        "user": user
    }

    try:
        response = httpx.post(f"{base_url}/run", json=payload, timeout=60.0)
        response.raise_for_status()
        result = response.json()
        
        # Format the output for the agent nicely
        console.print("[bold green]Workflow executed successfully:[/bold green]")
        if "data" in result and "outputs" in result["data"]:
            console.print(json.dumps(result["data"]["outputs"], indent=2, ensure_ascii=False))
        else:
            console.print(json.dumps(result, indent=2, ensure_ascii=False))
            
    except httpx.HTTPStatusError as e:
        console.print(f"[bold red]HTTP Error executing workflow:[/bold red] {e.response.text}")
    except Exception as e:
        console.print(f"[bold red]Error executing workflow:[/bold red] {str(e)}")

@dify_group.command(name="list")
@click.pass_context
def list_connectors(ctx: click.Context):
    """List available Dify connectors to use with the run command."""
    host = ctx.obj.get("host", "127.0.0.1")
    port = ctx.obj.get("port", 8088)
    base_url = f"http://{host}:{port}/api/enterprise/dify"

    try:
        response = httpx.get(f"{base_url}/connectors", timeout=10.0)
        response.raise_for_status()
        connectors = response.json()
        
        if not connectors:
            console.print("No Dify connectors configured.")
            return

        for c in connectors:
            status = "[green]Active[/green]" if c["is_active"] else "[red]Inactive[/red]"
            console.print(f"- ID: [bold]{c['id']}[/bold] | Name: {c['name']} | Status: {status}")
            
    except httpx.HTTPStatusError as e:
        console.print(f"[bold red]HTTP Error listing connectors:[/bold red] {e.response.text}")
    except Exception as e:
        console.print(f"[bold red]Error listing connectors:[/bold red] {str(e)}")
