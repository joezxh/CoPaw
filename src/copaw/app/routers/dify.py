from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel

from ..dependencies import get_db, require_admin
from ...db.models.dify import DifyConnector
from ...enterprise.dify_client import DifyClient

router = APIRouter(prefix="/api/enterprise/dify", tags=["Enterprise Dify"])

class DifyConnectorCreate(BaseModel):
    name: str
    description: str | None = None
    api_url: str
    api_key: str
    is_active: bool = True

class DifyConnectorUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    api_url: str | None = None
    api_key: str | None = None
    is_active: bool | None = None

class DifyConnectorResponse(BaseModel):
    id: str
    name: str
    description: str | None
    api_url: str
    is_active: bool
    
    class Config:
        orm_mode = True

@router.get("/connectors", response_model=List[DifyConnectorResponse])
async def list_connectors(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DifyConnector).order_by(DifyConnector.created_at.desc()))
    return result.scalars().all()

@router.post("/connectors", response_model=DifyConnectorResponse)
async def create_connector(data: DifyConnectorCreate, db: AsyncSession = Depends(get_db)):
    try:
        # Validate connection before saving
        client = DifyClient(data.api_url, data.api_key)
        # Attempt to get app parameters to verify api key
        await client.get_app_parameters(user="system_validation")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to validate Dify connection: {str(e)}")

    connector = DifyConnector(**data.dict())
    db.add(connector)
    await db.commit()
    await db.refresh(connector)
    return connector

@router.put("/connectors/{connector_id}", response_model=DifyConnectorResponse)
async def update_connector(connector_id: str, data: DifyConnectorUpdate, db: AsyncSession = Depends(get_db)):
    connector = await db.get(DifyConnector, connector_id)
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
        
    update_data = data.dict(exclude_unset=True)
    
    # If API details are updated, we should validate again
    if "api_url" in update_data or "api_key" in update_data:
        test_url = update_data.get("api_url", connector.api_url)
        test_key = update_data.get("api_key", connector.api_key)
        try:
            client = DifyClient(test_url, test_key)
            await client.get_app_parameters(user="system_validation")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to validate Dify connection: {str(e)}")

    for key, value in update_data.items():
        setattr(connector, key, value)
        
    await db.commit()
    await db.refresh(connector)
    return connector

@router.delete("/connectors/{connector_id}")
async def delete_connector(connector_id: str, db: AsyncSession = Depends(get_db)):
    connector = await db.get(DifyConnector, connector_id)
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
        
    await db.delete(connector)
    await db.commit()
    return {"detail": "Connector deleted successfully"}

class DifyWebhookPayload(BaseModel):
    task_id: str
    message_id: str | None = None
    event: str  # e.g. "workflow_finished", "workflow_failed", "message_end"
    data: dict

@router.post("/webhook")
async def dify_webhook_callback(payload: DifyWebhookPayload, db: AsyncSession = Depends(get_db)):
    """
    Callback endpoint for Dify workflow execution status updates.
    Dify will send POST requests here when workflows complete or fail.
    """
    # Here we would typically:
    # 1. Update the local WorkflowExecution record status based on payload.task_id
    # 2. Trigger a notification back to the CoPaw Agent or User (e.g. via WebSocket or Msg injection)
    
    # Example logic (placeholder for actual Task/Workflow integration):
    # execution = await db.execute(select(WorkflowExecution).where(WorkflowExecution.dify_task_id == payload.task_id))
    # ... update status ...
    
    print(f"[DIFY WEBHOOK] Task {payload.task_id} Event {payload.event} Data: {payload.data}")
    return {"status": "ok"}

class DifyRunPayload(BaseModel):
    connector_id: str
    inputs: dict
    user: str

@router.post("/run")
async def run_dify_workflow(payload: DifyRunPayload, db: AsyncSession = Depends(get_db)):
    """
    Run a Dify workflow via a specific connector. 
    Usually called by the dify_workflow CoPaw Skill via CLI.
    """
    connector = await db.get(DifyConnector, payload.connector_id)
    if not connector or not connector.is_active:
        raise HTTPException(status_code=404, detail="Active Dify Connector not found")
        
    client = DifyClient(connector.api_url, connector.api_key)
    try:
        # We use blocking here for simplicity in the CLI tool. 
        # For real scenarios, streaming or async webhooks are preferred.
        result = await client.run_workflow(payload.inputs, payload.user, response_mode="blocking")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

