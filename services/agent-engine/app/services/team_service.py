"""Team service — CRUD for saved multi-agent workflows."""

from __future__ import annotations

from datetime import datetime

from sqlmodel import Session, select

from ..db.models import Team
from ..schemas.team import TeamCreate, TeamUpdate


class TeamService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_teams(self) -> list[Team]:
        return list(self._session.exec(select(Team).order_by(Team.created_at.desc())).all())

    def get_team(self, team_id: int) -> Team | None:
        return self._session.get(Team, team_id)

    def create_team(self, data: TeamCreate) -> Team:
        team = Team(
            name=data.name,
            steps=[s.model_dump() for s in data.steps],
            working_file=data.working_file,
        )
        self._session.add(team)
        self._session.commit()
        self._session.refresh(team)
        return team

    def update_team(self, team_id: int, data: TeamUpdate) -> Team | None:
        team = self._session.get(Team, team_id)
        if team is None:
            return None
        values = data.model_dump(exclude_unset=True)
        if "steps" in values and values["steps"] is not None:
            values["steps"] = [dict(s) for s in values["steps"]]
        for key, value in values.items():
            setattr(team, key, value)
        team.updated_at = datetime.now()
        self._session.add(team)
        self._session.commit()
        self._session.refresh(team)
        return team

    def delete_team(self, team_id: int) -> bool:
        team = self._session.get(Team, team_id)
        if team is None:
            return False
        self._session.delete(team)
        self._session.commit()
        return True
