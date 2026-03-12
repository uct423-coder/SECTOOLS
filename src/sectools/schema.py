"""Pydantic schema for SecTools configuration validation."""

from __future__ import annotations
from typing import Any
from pydantic import BaseModel, ConfigDict, field_validator


ALLOWED_THEMES = {"cyan", "green", "red", "blue", "magenta"}


class WorkflowStep(BaseModel):
    """A single step in a workflow pipeline."""
    tool: str
    args: list[str] = []
    label: str = ""
    needs_wordlist: bool = False
    needs_url: bool = False
    interactive: bool = False
    group: int | None = None

    model_config = ConfigDict(extra="allow")


class Workflow(BaseModel):
    """A named workflow with description and steps."""
    description: str = ""
    steps: list[WorkflowStep] = []

    model_config = ConfigDict(extra="allow")


class SecToolsConfig(BaseModel):
    """Root configuration schema for SecTools."""
    default_wordlist: str = ""
    default_dirwordlist: str = ""
    notifications_enabled: bool = True
    theme_color: str = "cyan"
    log_retention_days: int = 30
    auto_save_targets: bool = False
    favorites: list[str] = []
    strict_scope: bool = False

    model_config = ConfigDict(extra="allow")

    @field_validator("theme_color")
    @classmethod
    def validate_theme(cls, v: str) -> str:
        if v not in ALLOWED_THEMES:
            return "cyan"
        return v

    @field_validator("log_retention_days")
    @classmethod
    def validate_retention(cls, v: int) -> int:
        if v < 1:
            return 1
        if v > 365:
            return 365
        return v
