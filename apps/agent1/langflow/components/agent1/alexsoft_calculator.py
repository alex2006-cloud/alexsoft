"""LangFlow tool component backed by the Agent1 calculator (`apps/agent1/calculator.py`).

Neither the math nor the tool description is reimplemented here: this wrapper loads the
same evaluator and the same prompt text the LangGraph agent uses, so both agents share
one whitelist, one set of limits and one set of error messages.
"""
from __future__ import annotations

import importlib.util
import os
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

from lfx.custom.custom_component.component import Component
from lfx.inputs.inputs import MessageTextInput
from lfx.io import Output
from lfx.schema.data import Data


def _agent1_dirs() -> Iterator[Path]:
    """Locate apps/agent1; LangFlow may exec this code without a real __file__."""
    agent1_dir = os.environ.get("ALEXSOFT_AGENT1_DIR")
    if agent1_dir:
        yield Path(agent1_dir)

    repo_root = os.environ.get("ALEXSOFT_REPO_ROOT")
    if repo_root:
        yield Path(repo_root) / "apps" / "agent1"

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        marker = Path(local_app_data) / "LangFlow" / "repo-root.txt"
        if marker.is_file():
            yield Path(marker.read_text(encoding="utf-8").strip()) / "apps" / "agent1"

    try:
        # apps/agent1/langflow/components/agent1/<this file> -> apps/agent1
        yield Path(__file__).resolve().parents[3]
    except NameError:
        pass


def load_agent1_module(module_name: str) -> ModuleType:
    """Import a top-level module of apps/agent1 by path, under a namespaced name."""
    tried: list[str] = []
    for directory in _agent1_dirs():
        path = directory / f"{module_name}.py"
        tried.append(str(path))
        if not path.is_file():
            continue
        spec = importlib.util.spec_from_file_location(f"alexsoft_agent1_{module_name}", path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    msg = (
        f"Не найден apps/agent1/{module_name}.py. Задайте ALEXSOFT_AGENT1_DIR или ALEXSOFT_REPO_ROOT "
        f"(start-langflow.ps1 делает это сам). Проверены пути: {', '.join(tried) or 'нет кандидатов'}"
    )
    raise FileNotFoundError(msg)


_prompts = load_agent1_module("prompts")
_calculator: ModuleType | None = None


def calculator_core() -> ModuleType:
    global _calculator
    if _calculator is None:
        _calculator = load_agent1_module("calculator")
    return _calculator


class AlexsoftCalculatorComponent(Component):
    display_name = "Alexsoft Calculator"
    description = _prompts.CALCULATOR_DESCRIPTION.splitlines()[0]
    icon = "calculator"
    name = "AlexsoftCalculator"

    inputs = [
        MessageTextInput(
            name="expression",
            display_name="Expression",
            info=_prompts.CALCULATOR_DESCRIPTION,
            tool_mode=True,
        ),
    ]

    outputs = [
        Output(display_name="Result", name="result", type_=Data, method="run_calculation"),
    ]

    def run_calculation(self) -> Data:
        core = calculator_core()
        expression = (self.expression or "").strip()
        try:
            detail = core.calculate(expression)
        except core.CalculatorError as exc:
            message = f"ERROR: {exc}"
            self.status = message
            return Data(data={"error": message, "input": expression})

        parsed, _, value = detail.rpartition(" = ")
        self.status = detail
        return Data(data={"result": value, "expression": parsed, "detail": detail})
