from typing import Any


def set_call_context(call_context: dict[str, Any]) -> None:
  """Stores the call context data.

  Args:
      call_context (dict[str, Any]): The call context data to store.

  Returns:
      None
  """
  context.state["called_set_call_context"] = True
  session_id = context.state.get("call_id", context.session_id)
  parameters = {
      "contextKey": session_id,
      "x-session-id": session_id,
      "X-Req-Param-contextKey": session_id,
  }

  try:
    parameters["sessionInfo"] = {
        "parameters": {"callContext": {"data": call_context}}
    }
    mock = context.state.get("mock_set_call_context_response")
    if mock:
      response = mock
    else:
      response = tools.call_context_postCallContextWithKey(parameters).json()

    if "sessionInfo" in response:
      print(f"INFO: Call context stored successfully with key: {session_id}")
    else:
      return _handle_error(f"response: {response}")
  except Exception as e:
    return _handle_error(f"tool call or response parsing failed - {e!r}")


def _handle_error(error_message: str) -> None:
  context.state["set_call_context_failure"] = error_message
  print(f"ERROR: set_call_context failed: {error_message}")
  # Return None on error, agent doesn't need to know
  # the tool call failed.
  return None
