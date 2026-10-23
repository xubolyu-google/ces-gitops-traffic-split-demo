from typing import Any


def get_home_appointment_arrival_time(appointment_ids: list[str]) -> dict[str, Any]:
  """Retrieves arrival information for multiple home appointments.

  Args:
      appointment_ids (list[str]): A list of appointment IDs to retrieve arrival info for.

  Returns:
      dict[str, Any]: A dictionary where each key is an appointment ID and the value is the corresponding arrival information.
  """
  if not appointment_ids:
    return _handle_error("appointment_ids is empty")

  session_id = context.state.get("call_id", context.session_id)
  parameters = {
      "appointmentIds": ",".join(appointment_ids),
      "x-request-id": session_id,
      "x-session-id": session_id,
      "x-sts-scope": "apid-int-cloud:GET,POST,PUT:/gw/dcpi-scheduling/api/**",
      "X-Resp-Payload-Tag": "arrivalTimeData",
  }

  try:
    mock = context.state.get("mock_get_home_appointment_arrival_time_response")
    if mock:
      response = mock
    else:
      response = tools.home_appointment_getArrivalTimes(parameters).json()

    if "sessionInfo" in response:
      data = response["sessionInfo"].get("parameters", {}).get("arrivalTimeData", {})
      return data
    else:
      return _handle_error(f"unexpected response: {response}")
  except Exception as e:
    return _handle_error(f"tool call or response parsing failed - {e!r}")


def _handle_error(error_message: str) -> dict[str, Any]:
  context.state["get_home_appointment_arrival_time_failure"] = error_message
  print(f"ERROR: get_home_appointment_arrival_time failed: {error_message}")
  return {}
