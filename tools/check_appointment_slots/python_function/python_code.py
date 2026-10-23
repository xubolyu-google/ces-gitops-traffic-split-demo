from typing import Any, Optional

# pylint: disable=undefined-variable

FAILURE_INSTRUCTION = """Inform the user that no appointment slots were found for their requested date and location. Then silently and immediately transition to the `Send_Self_Service_SMS` step."""




def check_appointment_slots(
    is_apple_device: bool,
) -> dict[str, Any]:
  """Retrieves up to 10 available instore appointment slots according to the user's location and date preference.

  ### PRE-REQUISITES:
  - You MUST have called `set_appointment_date_preference` and
  `set_appointment_location_preference` before calling this tool.

  Args:
    is_apple_device (bool): Set to True if the product brand is 'Apple' or the
      product is an Apple-branded device (e.g., MacBook, iPad). For all
      non-Apple devices (e.g., Windows, Microsoft, Dell) set this to False.

  Returns:
    dict[str, Any]: A dictionary containing the store name, ID, and an array of
    available ISO-8601 appointment timestamps, or an error message.

    Success Schema:
      - storeName (str): The display name of the store.
      - storeId (str): The store identifier.
      - slotTime (list[str]): List of available appointment slot timestamps in
        the store's local timezone (e.g., '2026-03-07T11:20:00.000-05:00').
        ISO-8601 format.

    Failure Schema:
      - agent_action (str): Explicit instructions that you, the AI agent, MUST
        follow immediately and exactly as written to recover from the failure.
  """
  start_date = context.state.get("appointment_start_date")
  end_date = context.state.get("appointment_end_date")
  at_local_store = context.state.get("appointment_at_local_store")
  zip_code = context.state.get("appointment_zip_code")

  if not start_date or not end_date:
    return {
        "agent_action": (
            "You must call `set_appointment_date_preference` first before"
            " calling `check_appointment_slots`."
        )
    }

  if at_local_store is None:
    return {
        "agent_action": (
            "You must call `set_appointment_location_preference` first before"
            " calling `check_appointment_slots`."
        )
    }

  session_id = context.state.get("call_id", context.session_id)
  request_params = {
      "startDate": start_date,
      "endDate": end_date,
      "ActivityType": "pr-appledrop" if is_apple_device else "pr-dropoff",
      "DepartmentId": "pr",
  }

  if at_local_store:
    request_params["StoreId"] = int(context.state["store_id"])
  else:
    request_params["ZipCode"] = zip_code

  parameters = {
      "x-session-id": session_id,
      "sessionInfo": {"parameters": {"request": request_params}},
  }

  try:
    mock = context.state.get("mock_get_appointment_slots_response")
    if mock:
      response = mock
    else:
      response = tools.instore_appointment_getAvailableSlotsBetweenDates(
          parameters
      ).json()

    if "sessionInfo" in response:
      data = response["sessionInfo"]["parameters"]["response"]

      if "storeName" in data:
        # We cache the store name here because users may have scheduled
        # an appointment using a zip code, meaning this will be different
        # from the store they were calling.
        context.variables["appointment_store_name"] = data["storeName"]

      return data
    else:
      return _handle_error(f"response: {response}")
  except Exception as e:
    return _handle_error(f"tool call or response parsing failed - {e!r}")


def _handle_error(error_message: str) -> dict[str, str]:
  context.state["check_appointment_slots_failure"] = error_message
  print(f"ERROR: check_appointment_slots failed: {error_message}")
  return {"agent_action": FAILURE_INSTRUCTION}
