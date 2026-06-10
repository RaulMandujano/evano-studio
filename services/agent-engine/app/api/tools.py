"""Tool catalog and test endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..core.errors import AppError
from ..schemas.tool import (
    ToolExecutionLogRead,
    ToolParamRead,
    ToolSpecRead,
    ToolTestRequest,
    ToolTestResponse,
)
from ..services.agent_service import AgentService
from ..services.tool_service import ToolService
from ..tools.registry import list_tools
from .deps import get_agent_service, get_tool_service

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("", response_model=list[ToolSpecRead], summary="List available tools")
def get_tools() -> list[ToolSpecRead]:
    return [
        ToolSpecRead(
            id=spec.id,
            name=spec.name,
            description=spec.description,
            category=spec.category,
            parameters=[ToolParamRead(**vars(p)) for p in spec.parameters],
            requires_approval=spec.requires_approval,
        )
        for spec in list_tools()
    ]


@router.get("/logs", response_model=list[ToolExecutionLogRead], summary="Recent tool executions")
def get_tool_logs(
    limit: int = 50,
    tools: ToolService = Depends(get_tool_service),
) -> list[ToolExecutionLogRead]:
    """Return recent tool-execution log entries (newest first). Metadata only."""
    return [ToolExecutionLogRead.model_validate(row) for row in tools.recent_logs(limit)]


@router.post("/test", response_model=ToolTestResponse, summary="Run a tool (test)")
def test_tool(
    payload: ToolTestRequest,
    tools: ToolService = Depends(get_tool_service),
    agents: AgentService = Depends(get_agent_service),
) -> ToolTestResponse:
    """Execute a tool with given params. If ``agent_id`` is provided, the agent's
    enabled-tools permission is enforced. Tool-level failures return ok=false."""
    agent = None
    if payload.agent_id is not None:
        agent = agents.get_agent(payload.agent_id)
        if agent is None:
            return ToolTestResponse(ok=False, message="Agent not found.")
    try:
        result = tools.execute(payload.tool_id, payload.params, agent=agent)
        return ToolTestResponse(ok=True, result=result)
    except AppError as exc:
        return ToolTestResponse(ok=False, message=exc.message)
    except Exception as exc:  # noqa: BLE001
        return ToolTestResponse(ok=False, message=f"Tool failed: {exc}")
