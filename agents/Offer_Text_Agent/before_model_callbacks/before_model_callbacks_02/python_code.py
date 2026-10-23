def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:

  played_sms_scheduling = callback_context.state.get("played_sms_scheduling_offer")
  played_sms_return_exchange = callback_context.state.get("played_should_play_sms_return_exchange")
  played_sms_mail_in_repair = callback_context.state.get("played_should_play_sms_mail_in_repair")

  # Hide disclosure tool only if no applicable offer has been played yet.
  # Only one path is active at a time, so once any played_* flag is set,
  # the disclosure should become available.
  if not (played_sms_scheduling or played_sms_return_exchange or played_sms_mail_in_repair):
    llm_request.config.hide_tool("play_message_data_rates_legal_disclosure")


  if not callback_context.state.get("played_message_data_rates_legal_disclosure"):
    # Disallow sending appointment link SMS without playing the
    # message and data rates legal disclosure message first.
    llm_request.config.hide_tool("send_appointment_link_sms_v2")

  return None
