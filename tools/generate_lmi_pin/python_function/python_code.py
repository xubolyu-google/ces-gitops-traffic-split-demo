"""Tool to generate a unique 6-digit PIN for LogMeIn remote support sessions."""

FAILURE_INSTRUCTION = """1. Say exactly: "I'm having some trouble setting up remote support, would you like to speak to a live agent?" Then wait for the user's response.
2. Carefully analyze the user's response:
  2a. If the user responds affirmatively: call {@TOOL: connect_to_computing_service_live_agent}.
  2b. If the user responds negatively: silently call the {@TOOL: call_wrapup} tool.
  2c. If the user responds ambiguously: seek clarification.
"""


def generate_lmi_pin() -> dict[str, str]:
  """Generates a unique 6-digit PIN for LogMeIn(LMI) remote support sessions.

  Returns:
    dict[str, Any]: A dictionary containing LMI PIN or an error message.

    Success Schema:
        - pin (str): The LMI PIN.

    Failure Schema:
      - agent_action (str): Explicit instructions that you, the AI agent, MUST
        follow immediately and exactly as written to recover from the failure.
  """
  session_id = context.state.get("call_id", context.session_id)
  parameters = {
      "x-request-id": session_id,
      "x-session-id": session_id,
      "sessionInfo": {"parameters": {"lmiRequest": {"callID": session_id}}},
  }
  try:
    mock = context.state.get("mock_get_lmi_pin_response")
    if mock:
      response = mock
    else:
      response = tools.LMI_getLmiPin(parameters).json()
    if "sessionInfo" in response:
      result = response["sessionInfo"]["parameters"]["lmiResponse"]
      context.state["initiated_lmi"] = True
      pin_value = result.get("pin", "")
      context.state["lmi_pin"] = str(int(pin_value)) if pin_value else ""
      return result
    else:
      return _handle_error(f"response: {response}")
  except Exception as e:
    return _handle_error(f"tool call or response parsing failed - {e!r}")


def _handle_error(error_message: str) -> dict[str, str]:
  context.state["generate_lmi_pin_failure"] = error_message
  print(f"ERROR: generate_lmi_pin failed: {error_message}")
  return {"agent_action": FAILURE_INSTRUCTION}
