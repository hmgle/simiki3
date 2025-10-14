"""Configuration models and helpers for the Simiki3 rewrite."""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, MutableMapping

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator


class ConfigError(ValueError):
    """Raised when configuration files are missing or invalid."""

    def __init__(self, message: str, *, validation_error: ValidationError | None = None) -> None:
        super().__init__(message)
        self.validation_error = validation_error


class SiteConfig(BaseModel):
    """Validated configuration for a wiki site."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    url: str = ""
    title: str = "Simiki Wiki"
    keywords: str = ""
    description: str = ""
    author: str = ""
    root: str = "/"
    source: str = "content"
    destination: str = "output"
    attach: str = "attach"
    themes_dir: str = "themes"
    theme: str = "simple2"
    default_ext: str = "md"
    pygments: bool = True
    debug: bool = False

    @field_validator("url")
    @classmethod
    def _trim_trailing_slash(cls, value: str) -> str:
        value = value.strip()
        if value.endswith("/"):
            value = value[:-1]
        return value

    @field_validator("root")
    @classmethod
    def _normalise_root(cls, value: str) -> str:
        value = value.strip() or "/"
        if not value.startswith("/"):
            raise ValueError("root must start with '/'")
        if len(value) > 1 and value.endswith("/"):
            value = value[:-1]
        return value

    @field_validator("source", "destination", "attach", "themes_dir", "theme")
    @classmethod
    def _strip_slashes(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("string value must not be empty")
        return value.strip("/ ")

    @field_validator("default_ext")
    @classmethod
    def _clean_extension(cls, value: str) -> str:
        value = value.strip().lstrip(".").lower()
        if not value:
            raise ValueError("default_ext must contain characters")
        return value

    def with_overrides(self, **overrides: Any) -> "SiteConfig":
        """Return a new config with fields replaced by ``overrides``."""
        try:
            return self.model_copy(update=overrides)
        except ValidationError as exc:  # pragma: no cover - delegated to pydantic
            raise ConfigError("Invalid configuration overrides", validation_error=exc) from exc

    def as_dict(self) -> dict[str, Any]:
        """Serialise the config to a standard dictionary."""
        return dict(self.model_dump())


def default_config() -> SiteConfig:
    """Return a copy of the default configuration."""
    return SiteConfig()


def load_config(config_path: Path, *, overrides: Mapping[str, Any] | None = None) -> SiteConfig:
    """Load and validate the site configuration from ``config_path``.

    Parameters
    ----------
    config_path:
        Path to the YAML configuration file (usually ``_config.yml``).
    overrides:
        Optional mapping applied on top of the file contents before validation.
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with io.open(config_path, "r", encoding="utf-8") as stream:
            data = yaml.safe_load(stream) or {}
    except yaml.YAMLError as exc:  # pragma: no cover - depends on lib internals
        raise ConfigError(f"Failed to parse YAML configuration: {exc}") from exc

    if not isinstance(data, MutableMapping):
        raise ConfigError("Configuration root must be a mapping of keys to values")

    merged: dict[str, Any] = {**default_config().as_dict(), **dict(data)}
    if overrides:
        merged.update(dict(overrides))

    try:
        return SiteConfig(**merged)
    except ValidationError as exc:
        raise ConfigError("Invalid configuration values", validation_error=exc) from exc


@dataclass(frozen=True)
class ConfigFiles:
    """Convenience container describing expected config file names."""

    main: str = "_config.yml"

    def resolve(self, base_path: Path) -> Path:
        """Return the absolute path to the main config file within ``base_path``."""
        return Path(base_path) / self.main
