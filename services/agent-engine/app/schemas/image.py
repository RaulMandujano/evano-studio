"""Schemas for ComfyUI settings/status and image generation."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ComfyUIStatusResponse(BaseModel):
    enabled: bool
    base_url: str
    reachable: bool
    version: Optional[str] = None
    default_workflow_path: str = ""
    message: Optional[str] = None


class ComfyUISettingsUpdate(BaseModel):
    base_url: Optional[str] = None
    enabled: Optional[bool] = None
    default_workflow_path: Optional[str] = None


class ComfyUISettingsRead(BaseModel):
    base_url: str
    enabled: bool
    default_workflow_path: str


class PromptTestRequest(BaseModel):
    prompt: str = Field(min_length=1)
    negative_prompt: str = ""
    workflow_name: Optional[str] = None


class PromptTestResponse(BaseModel):
    ok: bool
    reachable: bool
    message: Optional[str] = None


class ImageGenerateRequest(BaseModel):
    prompt: str = Field(min_length=1)
    negative_prompt: str = ""
    workflow_name: Optional[str] = None
    agent_id: Optional[int] = None


class ImageGenerationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prompt: str
    negative_prompt: Optional[str] = None
    workflow_name: Optional[str] = None
    status: str
    output_path: Optional[str] = None
    error: Optional[str] = None
    created_by_agent_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
