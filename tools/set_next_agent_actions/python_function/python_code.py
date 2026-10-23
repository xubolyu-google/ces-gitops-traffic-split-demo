# pylint: disable=undefined-variable
from typing import Any, Optional


def set_next_agent_actions(
    customized_response: Optional[dict[str, Any]] = None,
    custom_payload: Optional[dict[str, Any]] = None,
    function_calls: Optional[list[dict[str, Any]]] = None,
    agent_transfer: Optional[dict[str, Any]] = None,
    end_session: Optional[dict[str, Any]] = None,
) -> None:
  """Override the next agent actions, bypassing LLM."""
  actions = context.state["next_agent_actions"] = {}
  if customized_response:
    actions["customized_response"] = customized_response
  if custom_payload:
    actions["custom_payload"] = custom_payload
  if function_calls:
    actions["function_calls"] = function_calls
  if agent_transfer:
    actions["agent_transfer"] = agent_transfer
  if end_session:
    actions["end_session"] = end_session
