"""Utilities for reading packaged resources from the installed wheel."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path


def read_resource_text(*parts: str) -> str:
    node = files("project_agent_framework")
    for part in parts:
        node = node.joinpath(part)
    return node.read_text(encoding="utf-8")


def copy_resource_tree(destination: Path, *parts: str) -> Path:
    node = files("project_agent_framework")
    for part in parts:
        node = node.joinpath(part)
    _copy_node(node, destination)
    return destination


def _copy_node(node, destination: Path) -> None:
    if node.is_file():
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(node.read_text(encoding="utf-8"), encoding="utf-8")
        return
    destination.mkdir(parents=True, exist_ok=True)
    for child in node.iterdir():
        _copy_node(child, destination / child.name)
