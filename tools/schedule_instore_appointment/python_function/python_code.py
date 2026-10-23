"""Tool to schedule an in-store appointment."""

import datetime
from typing import Optional


# pylint: disable=undefined-variable

FAILURE_INSTRUCTION = """You MUST inform the user that the appointment could not be scheduled successfully. Say exactly: "I'm sorry, I'm having some trouble scheduling the appointment right now. To schedule an appointment, you can go to bestbuy.com and find the 'Schedule a Service' page there." Then silently and immediately transition to the `Send_Self_Service_SMS` step."""


def schedule_instore_appointment(
    store_id: int,
    is_apple_device: bool,
    appointment_date_time: str,
    notes: Optional[str] = None,
) -> str:
  """Schedules an in-store appointment for a customer.

  The Agent MUST strictly execute the instructions returned by this tool without
  deviation.

  Args:
    store_id (int): The store ID where the appointment will be created (from
      check_appointment_slots).
    is_apple_device (bool): Set to True if the product is an Apple-branded
      device (e.g., MacBook, iPad).
    appointment_date_time (str): The EXACT timestamp string returned by the
      `check_appointment_slots` tool corresponding to the appointment slot that
      the user selected. It is CRITICAL that you DO NOT alter the timestamp in any way.
    notes (str, optional): Additional appointment notes.

  Returns:
      str: A mandatory instruction set that the agent MUST follow to continue
        the conversation flow.
  """
  context.state["should_transfer_to_graceful_signoff"] = True

  session_id = context.state.get("call_id", context.session_id)
  if "customer_phone_number" not in context.state:
    return _handle_error("customer_phone_number not set")
  if "first_name" not in context.state:
    return _handle_error("first_name not set")
  party_ids = context.state.get("party_ids", [])
  if not party_ids:
    return _handle_error("party_ids not set")

  request_payload = {
      "storeId": store_id,
      "departmentId": "pr",
      "activityType": "pr-appledrop" if is_apple_device else "pr-dropoff",
      "createdBy": "NGA",
      "appointmentDateTime": appointment_date_time,
      "clientExternalId": party_ids[0],
  }

  request_payload["firstName"] = context.state["first_name"]
  request_payload["phoneNumber"] = context.state["customer_phone_number"]
  request_payload["smsPhoneNumber"] = context.state["customer_phone_number"]
  if notes:
    request_payload["notes"] = notes
  if "last_name" in context.state:
    request_payload["lastName"] = context.state["last_name"]
  if "email" in context.state:
    request_payload["email"] = context.state["email"]

  parameters = {
      "x-session-id": session_id,
      "sessionInfo": {"parameters": {"request": request_payload}},
  }

  try:
    # Format apt time for confirmation message (e.g., Saturday, January 3
    # at 8:20 PM). Done before the API call so that we fail fast and
    # don't make a phantom booking in the unlikely event that this fails.
    parsed_appointment_time = datetime.datetime.fromisoformat(appointment_date_time)
    formatted_date = parsed_appointment_time.strftime("%A, %B %-d")
    formatted_time = parsed_appointment_time.strftime("%-I:%M %p")

    mock = context.state.get("mock_create_appointment_response")
    if mock:
      response = mock
    else:
      response = tools.instore_appointment_createAppointment(parameters).json()

    if "sessionInfo" in response:
      data = response["sessionInfo"]["parameters"]["response"]
      if "confirmationNumber" in data:
        store_name = context.state.get("appointment_store_name")
        location_text = (
            f"at Best Buy {store_name}" if store_name else "in store"
        )

        system_instruction = (
            "Inform the user of their scheduled appointment, adhering to the"
            ' exact template: "Great! We will see you'
            f" {location_text} on {formatted_date}, at {formatted_time}."
            " To manage this appointment, visit your Appointments page in your"
            " Account on BestBuy.com. During your appointment, if any"
            " additional services are needed or requested, additional charges"
            " may apply and would require your approval. Please remember any"
            " power cords, cables and additional accessories needed to"
            " replicate the issues you're experiencing, so we may provide the"
            ' best service possible.". It is vital to strictly adhere to this'
            " verbiage because it contains important disclaimers."
        )

        return system_instruction
    else:
      return _handle_error(f"response: {response}")
  except Exception as e:
    return _handle_error(f"tool call or response parsing failed - {e!r}")


def _handle_error(error_message: str) -> str:
  context.state["schedule_instore_appointment_failure"] = error_message
  print(f"ERROR: schedule_instore_appointment failed: {error_message}")
  return FAILURE_INSTRUCTION
