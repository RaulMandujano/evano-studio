"""Approval endpoints for agent-proposed sensitive actions (human-in-the-loop).

An agent never runs a computer-control action on its own — it creates a
PendingAction, and the user approves or denies it here. Approving runs the action
through ToolService (permission-gated + logged); denying records the refusal.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlmodel import Session, desc, select

from ..core.errors import AppError
from ..db.models import Agent, PendingAction
from ..schemas.action import ActionResolveResponse, PendingActionRead
from ..schemas.tool import ToolExecution
from ..services.tool_service import ToolService
from ..db.session import get_session
from ..utils.time import utc_now
from .deps import get_tool_service

router = APIRouter(prefix="/actions", tags=["actions"])
logger = logging.getLogger("evano.agent_engine.agents")


@router.get("", response_model=list[PendingActionRead], summary="List pending actions")
def list_actions(
    status: str = "pending",
    limit: int = 50,
    session: Session = Depends(get_session),
) -> list[PendingActionRead]:
    limit = max(1, min(limit, 200))
    rows = session.exec(
        select(PendingAction)
        .where(PendingAction.status == status)
        .order_by(desc(PendingAction.created_at))
        .limit(limit)
    ).all()
    return [PendingActionRead.model_validate(r) for r in rows]


@router.post("/{action_id}/approve", response_model=ActionResolveResponse, summary="Approve an action")
def approve_action(
    action_id: int,
    session: Session = Depends(get_session),
    tools: ToolService = Depends(get_tool_service),
) -> ActionResolveResponse:
    """Run the approved action now. The action is executed exactly as proposed."""
    action = session.get(PendingAction, action_id)
    if action is None:
        return ActionResolveResponse(ok=False, status="not_found", message="Action not found.")
    if action.status != "pending":
        return ActionResolveResponse(
            ok=False, status="already_resolved", message=f"Action is already {action.status}."
        )

    agent = session.get(Agent, action.agent_id) if action.agent_id is not None else None
    try:
        result = tools.execute(action.tool_id, action.args or {}, agent=agent, source="agent-approved")
    except AppError as exc:
        action.status = "error"
        action.error = exc.message
        action.resolved_at = utc_now()
        session.add(action)
        session.commit()
        logger.warning("approved action failed: id=%s tool=%s err=%s", action_id, action.tool_id, exc.message)
        return ActionResolveResponse(
            ok=False, status="error", message=exc.message,
            execution=ToolExecution(
                tool_id=action.tool_id, tool_name=action.tool_name, ok=False,
                summary=action.summary, message=exc.message,
            ),
        )

    action.status = "done"
    action.result = (result.get("message") if isinstance(result, dict) else None) or "Done."
    action.resolved_at = utc_now()
    session.add(action)
    session.commit()
    logger.info("approved action done: id=%s tool=%s", action_id, action.tool_id)
    return ActionResolveResponse(
        ok=True, status="done",
        execution=ToolExecution(
            tool_id=action.tool_id, tool_name=action.tool_name, ok=True,
            summary=action.summary, result=result,
        ),
    )


@router.post("/{action_id}/deny", response_model=ActionResolveResponse, summary="Deny an action")
def deny_action(
    action_id: int,
    session: Session = Depends(get_session),
) -> ActionResolveResponse:
    action = session.get(PendingAction, action_id)
    if action is None:
        return ActionResolveResponse(ok=False, status="not_found", message="Action not found.")
    if action.status != "pending":
        return ActionResolveResponse(
            ok=False, status="already_resolved", message=f"Action is already {action.status}."
        )
    action.status = "denied"
    action.resolved_at = utc_now()
    session.add(action)
    session.commit()
    logger.info("denied action: id=%s tool=%s", action_id, action.tool_id)
    return ActionResolveResponse(ok=True, status="denied", message="Action denied.")
