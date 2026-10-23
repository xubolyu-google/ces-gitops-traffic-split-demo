"""Tool to schedule an in-store appointment."""

import datetime
from typing import Optional


# pylint: disable=undefined-variable

FAILURE_INSTRUCTION = """You MUST inform the user that the appointment could not be scheduled successfully. Say exactly: "I'm sorry, I'm having some trouble scheduling the appointment right now. To schedule an appointment, you can go to bestbuy.com and find the 'Schedule a Service' page there." Then silently and immediately transition to the `Send_Self_Service_SMS` step."""


def create_appointment(
    store_id: int,
    is_apple_device: bool,
    appointment_date_time: str,
    appointment_notes: str,
) -> str:
  """Schedules an in-store appointment for a customer.

  The Agent MUST strictly execute the instructions returned by this tool without
  deviation.

  Args:
    store_id (int): The store ID where the appointment will be created (from
      check_appointment_slots).
    is_apple_device (bool): Set to True if the product brand is 'Apple' or the
      product is an Apple-branded device (e.g., MacBook, iPad). For all
      non-Apple devices (e.g., Windows, Microsoft, Dell) set this to False.
    appointment_date_time (str): The EXACT timestamp string returned by the
      `check_appointment_slots` tool corresponding to the appointment slot that
      the user selected. It is CRITICAL that you DO NOT alter the timestamp in any way.
    appointment_notes (str): A detailed summary of the customer's issue to be
      saved as notes for their in-store appointment.
      - FORMAT: Professional, third-person narrative.
      - CONTENT: Include the following ONLY if they have been explicitly
       disclosed in the conversation:
       1. The specific issue and device details.
       2. Troubleshooting steps attempted during this session and their outcomes.
       3. The reason for scheduling an in-store appointment (e.g., hardware
         repair needed, in-person diagnosis required, or user preference).
       4. Any additional details that the in-store technician should be aware of
         (e.g., accessories needed, visible damage, error codes).
      - DATA INTEGRITY: Do not infer or hallucinate details (like device
        models or specific errors) if the user has not provided them. If a
        category is unknown, omit it.
      - CRITICAL: This is the in-store technician's first point of context.
        Accuracy is paramount to avoid making the customer repeat themselves
        during their appointment.
      - EXAMPLE (Full Context): "User's MacBook Pro is experiencing persistent
        latency. Guided user through a hard reboot, but performance did not
        improve. In-store appointment scheduled for hardware diagnosis as
        remote troubleshooting was unsuccessful."
      - EXAMPLE (Limited Context): "User reported that their tablet screen is
        cracked but did not specify the device model. In-store appointment
        scheduled per user request for repair assessment."

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
  request_payload["notes"] = appointment_notes
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
  context.state["create_appointment_failure"] = error_message
  print(f"ERROR: create_appointment failed: {error_message}")
  return FAILURE_INSTRUCTION
