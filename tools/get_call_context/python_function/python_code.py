from typing import Any

KEEP_FIELDS = "phoneNumber"


def get_call_context() -> dict[str, Any]:
  """Retrieves the contextual metadata for the current customer call.

  Returns:
      dict[str, Any]: A dictionary containing call context.
      Schema:
          - phoneNumber (str): The 10-digit phone number of the caller.
  """
  session_id = context.state.get("call_id", context.session_id)
  parameters = {"contextKey": session_id, "x-session-id": session_id}
  try:
    mock = context.state.get("mock_get_call_context_response")
    if mock:
      response = mock
    else:
      response = tools.call_context_getCallContext(parameters).json()
    if "sessionInfo" in response:
      data = response["sessionInfo"]["parameters"]["callContext"]["data"]
      context.state["call_context"].update(data)
      context.state["dfcx_params"].update(data)
      context.state["customer_phone_number"] = data.get("phoneNumber")
      context.state["entry_point_phone_number"] = data.get("entryPointNumber")
      return {k: data[k] for k in KEEP_FIELDS if k in data}
    else:
      return _handle_error(f"response: {response}")
  except Exception as e:
    return _handle_error(f"tool call or response parsing failed - {e!r}")


def _handle_error(error_message: str) -> dict[str, Any]:
  context.state["get_call_context_failure"] = error_message
  print(f"ERROR: get_call_context failed: {error_message}")
  # Return empty result on error, agent doesn't need to know
  # the tool call failed.
  return {}
