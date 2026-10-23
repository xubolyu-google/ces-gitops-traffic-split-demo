from typing import Any


def ani_denylist_lookup() -> dict[str, Any]:
  """Checks if the customer's phone number(ANI - Automatic Number Identification) is present in the denylist.

  Returns:
    dict[str, Any]: A dictionary containing ANI denylist result.
    Schema:
        - isANIDenyListed (bool): Indicates if the ANI is in the denylsit.
  """
  if "customer_phone_number" not in context.state:
    return _handle_error("customer_phone_number not set")

  session_id = context.state.get("call_id", context.session_id)
  parameters = {
      "x-session-id": session_id,
      "sessionInfo": {
          "parameters": {"PhoneNumber": context.state["customer_phone_number"]}
      },
  }
  try:
    mock = context.state.get("mock_ani_denylist_response")
    if mock:
      response = mock
    else:
      response = tools.ANI_aniDenyList(parameters).json()
    if "sessionInfo" in response:
      data = response["sessionInfo"]["parameters"]
      context.state["dfcx_params"].update(data)
      return {"isANIDenyListed": data["isANIDenyListed"].lower() == "true"}
    else:
      return _handle_error(f"response: {response}")
  except Exception as e:
    return _handle_error(f"tool call or response parsing failed - {e!r}")


def _handle_error(error_message: str) -> dict[str, Any]:
  context.state["ani_denylist_lookup_failure"] = error_message
  print(f"ERROR: ani_denylist_lookup failed: {error_message}")
  # Return empty result on error, agent doesn't need to know
  # the tool call failed.
  return {}
