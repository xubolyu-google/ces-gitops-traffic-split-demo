# pylint: disable=missing-function-docstring,missing-class-docstring,missing-module-docstring,invalid-name,undefined-variable,line-too-long


OFFER_TEXT_TEMPLATE = """
<step name="Offer_SMS">
  <trigger>Immediately on agent start without waiting for a user utterance.</trigger>
  <action>
    1. You MUST silently call {@TOOL: play_message_data_rates_legal_disclosure}.
    2. Wait for the user to answer before continuing.
    3. Analyze the user's response:
      Analyze the user's response:
        3a. If the user responds affirmatively, call {@TOOL: send_appointment_link_sms_v2} without any arguments.
        3b. If the user responds negatively, ask for an alternate phone number. Wait for an answer, then analyze their response:
            - If the user provides an alternate number that is not a valid 10-digit US number, tell the user their number doesn't look valid and ask them for a valid one (e.g., 'The phone number 111222333 doesn't look valid, can you please provide a valid 10 digit phone number?'). Wait for an answer before continuing.
            - If the user provides a valid 10-digit phone number, call {@TOOL: set_alternative_sms_number_v2} with the new number.
            - If the user declines to provide an alternate number, silently and immediately call the {@TOOL: call_wrapup} tool.
  </action>
</step>
"""




def before_agent_callback(
    callback_context: CallbackContext,
) -> Optional[Content]:
  variables = callback_context.variables
  # ONLY update the instruction variable once.
  if not variables.get("offer_text_instruction"):
    variables["offer_text_instruction"] = OFFER_TEXT_TEMPLATE