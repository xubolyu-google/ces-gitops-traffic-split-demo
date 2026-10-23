FAILURE_INSTRUCTION = """You MUST inform the user that the text was not sent successfully (e.g. "I'm sorry, I'm having some trouble sending the text message right now. You can go to bestbuy.com to find the relevant page there.")."""
SUCCESS_INSTRUCTION = """You MUST inform the user that the text has been sent (e.g. "OK. The text is on the way.") before continuing."""


def send_sms(
    use_alternative_number: bool = False,
) -> str:
  """Sends a self-service SMS link to the user (e.g. for scheduling an appointment, order status, price match, or return/exchange).

  The Agent MUST strictly execute the instructions returned by this tool without
  deviation.

  Args:
      use_alternative_number (bool): Set to True when the customer wants to receive
                            the SMS to an alternative number and the provided alternative
                            number has been set by the set_alternative_sms_number tool.

  Returns:
      str: A mandatory instruction set that the agent MUST follow to continue
        the conversation flow.
  """
  event_id = context.state.get("sms_link_event_id", "IVR_IS_Schedule")

  # For Computer Troubleshooting (IVR_IS_Schedule), make sure the message and data rates
  # legal disclosure is played before sending the sms.
  if not context.state.pop("played_message_data_rates_legal_disclosure", False):
    return (
        "You MUST call {@TOOL: play_sms_legal_disclosure} and obtain user"
        " consent before calling this function."
    )

  # 1. Determine which key to look for in context.state
  phone_key = "alternative_sms_number" if use_alternative_number else "customer_phone_number"

  # 2. Validation check for the required number
  sms_number = context.state.get(phone_key)
  if not sms_number:
    return _handle_error(f"{phone_key} not set")

  req = {
    "eventId": event_id,
    "sessionId": context.session_id,
    "customer": {
      "phoneNumber": sms_number
    }
  }
  if fields := context.state.get("sms_fields"):
    req["fields"] = fields
  parameters = {
      "x-session-id": context.session_id,
      "sessionInfo": {
          "parameters": {
              "sendSMSReq": req
          }
      }
  }
  try:
    mock = context.state.get("mock_send_sms_response")
    if mock:
      response = mock
    else:
      response = tools.SMS_sendSmsToCustomer(parameters).json()
    if (
        response["sessionInfo"]["parameters"]["sendSMSResp"]["message"]
        == "sent"
    ):
      return SUCCESS_INSTRUCTION
    else:
      return _handle_error(f"response: {response}")
  except Exception as e:
    return _handle_error(f"tool call or response parsing failed - {e!r}")


def _handle_error(error_message: str) -> str:
  context.state["send_appointment_link_sms_failure"] = error_message
  print(f"ERROR: send_sms failed: {error_message}")
  return FAILURE_INSTRUCTION