"""Agent service — CRUD for local agents (no HTTP here)."""

from __future__ import annotations

from sqlmodel import Session, select

from ..db.models import Agent
from ..schemas.agent import AgentCreate, AgentUpdate
from ..utils.time import utc_now


class AgentService:
    """Create, read, update, and delete local agents."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_agents(self) -> list[Agent]:
        return list(self._session.exec(select(Agent).order_by(Agent.created_at)).all())

    def get_agent(self, agent_id: int) -> Agent | None:
        return self._session.get(Agent, agent_id)

    def create_agent(self, data: AgentCreate) -> Agent:
        agent = Agent(**data.model_dump())
        self._session.add(agent)
        self._session.commit()
        self._session.refresh(agent)
        return agent

    def update_agent(self, agent_id: int, data: AgentUpdate) -> Agent | None:
        agent = self._session.get(Agent, agent_id)
        if agent is None:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(agent, key, value)
        agent.updated_at = utc_now()
        self._session.add(agent)
        self._session.commit()
        self._session.refresh(agent)
        return agent

    def delete_agent(self, agent_id: int) -> bool:
        agent = self._session.get(Agent, agent_id)
        if agent is None:
            return False
        self._session.delete(agent)
        self._session.commit()
        return True
