def fetch_init_json() -> None:
  """Fetch the initialize parameters for emergency messages and DFCX transfer."""
  session_id = context.state.get("call_id", context.session_id)
  parameters = {
      "sessionInfo": {
          "parameters": {},
          "session": (
              f"projects/bbyus-ana-ccai-care-d01/locations/us-central1/agents/245f05ad-ed15-454e-b8bb-38109ac59a42/sessions/{session_id}"
          ),
      },
      "fulfillmentInfo": {"tag": "fetch_init_json"},
  }

  try:
    mock = context.state.get("mock_fetch_init_json_response")
    if mock:
      response = mock
    else:
      response = tools.init_json_fetchInitJson(parameters).json()
    if "sessionInfo" in response:
      data = response["sessionInfo"]["parameters"]
      context.state["init_json"] = data
      context.state["emergency_message_national"] = data.get(
          "defaultStart_emergencyMessage_national"
      )
      context.state["emergency_message_retail"] = data.get(
          "defaultStart_emergencyMessage_retail"
      )
      print("INFO: Initialize parameters fetched successfully")
    else:
      return _handle_error(f"response: {response}")
  except Exception as e:
    return _handle_error(f"tool call or response parsing failed - {e!r}")


def _handle_error(error_message: str) -> None:
  context.state["fetch_init_json_failure"] = error_message
  print(f"ERROR: fetch_init_json failed: {error_message}")
  # Return None on error, agent doesn't need to know
  # the tool call failed.
  return None
