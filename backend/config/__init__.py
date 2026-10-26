"""Configuration management."""

# Re-export the one instance from settings.py. A second Settings() here meant modules importing
# backend.config and backend.config.settings held different objects, so an override set on one
# never reached the other.
from .settings import Settings, settings

__all__ = ['Settings', 'settings']
