FAILURE_INSTRUCTION = """You MUST inform the user that the text was not sent successfully (e.g. "I'm sorry, I'm having some trouble sending the text message right now. """
SUCCESS_INSTRUCTION = """You MUST inform the user that the text has been sent (e.g. "OK. The text is on the way.")."""


def send_appointment_link_sms_v2(use_alternative_number: bool = False) -> str:
  """Sends a self-service SMS link to the user for scheduling an in-store appointment.

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
  # Makes sure the legal disclosure is played and pops it so that for the
  # edge case where the user has another issue and comes back to
  # troubleshooting, we will require legal disclosure to be played again.
  if not context.state.pop("played_message_data_rates_legal_disclosure", False):
    return (
        "You MUST call {@TOOL: play_message_data_rates_legal_disclosure} and obtain user"
        " consent before calling this function."
    )

  context.state["should_transfer_to_graceful_signoff"] = True
  # 1. Determine which key to look for in context.state
  phone_key = "alternative_sms_number" if use_alternative_number else "customer_phone_number"

  # 2. Validation check for the required number
  sms_number = context.state.get(phone_key)

  if not sms_number:
    return _handle_error(f"{phone_key} not set")

  sms_request = {
      "eventId": context.state.get("sms_event_id"),
      "sessionId": context.session_id,
      "customer": {
          "phoneNumber": sms_number
      }
  }

  page_title = context.state.get("page_title")
  page_link = context.state.get("page_link")

  if page_title and page_link:
      sms_request["fields"] = {
          "nonSensitiveInformationLink": page_title,
          "version": page_link
      }

  parameters = {
      "x-session-id": context.session_id,
      "sessionInfo": {
          "parameters": {
              "sendSMSReq": sms_request
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
  print(f"ERROR: send_appointment_link_sms failed: {error_message}")
  return FAILURE_INSTRUCTION
