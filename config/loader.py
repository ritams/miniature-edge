from __future__ import annotations
import pathlib
import yaml
from .models import Settings


def load_settings(path: str | pathlib.Path) -> Settings:
    """Load YAML config into typed Settings.

    Args:
        path: path to YAML file
    Returns:
        Settings instance validated by pydantic
    """
    p = pathlib.Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return Settings.model_validate(data)
