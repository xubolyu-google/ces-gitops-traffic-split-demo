from typing import Any
"""Tool to check the status of a user's LMI connection."""


def check_lmi_status() -> dict[str, Any]:
  """Retrieve the LogMeIn(LMI) remote support session status.

  Returns:
    The LMI status.
  """
  session_id = context.state.get("call_id", context.session_id)
  parameters = {
      "x-request-id": session_id,
      "x-session-id": session_id,
      "sessionInfo": {"parameters": {"lmiRequest": {"callID": session_id}}},
  }
  try:
    mock = context.state.get("mock_get_lmi_status_response")
    if mock:
      response = mock
    else:
      response = tools.LMI_getLmiStatus(parameters).json()
    if "sessionInfo" in response:
      data = response["sessionInfo"]["parameters"]["lmiResponse"]
      return data
    print(f"ERROR: Failed to fetch LMI status, got result {response}")
  except Exception as e:
    print(f"ERROR: Failed to fetch LMI status - {e!r}")

  return "UNKNOWN"
