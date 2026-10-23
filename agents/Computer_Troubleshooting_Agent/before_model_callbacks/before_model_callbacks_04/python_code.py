def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
  if (
      not callback_context.state.get("appointment_start_date")
      or callback_context.state.get("appointment_at_local_store") is None
  ):
    # Disallow calling check_appointment_slots without gathering user's
    # location and date preference first.
    llm_request.config.hide_tool("check_appointment_slots")

  if callback_context.state.get("appointment_store_name") is None:
    # Disallow calling create_appointment without calling
    # check_appointment_slots first.
    llm_request.config.hide_tool("create_appointment")

  if not callback_context.state.get("party_ids"):
    # Disallow appointment related tools since the agent cannot schedule
    # an appointment without a party id.
    llm_request.config.hide_tool("set_appointment_date_preference")
    llm_request.config.hide_tool("set_appointment_location_preference")
    llm_request.config.hide_tool("check_appointment_slots")
    llm_request.config.hide_tool("create_appointment")

  if not callback_context.state.get("played_sms_scheduling_offer"):
    # Disallow sending message and data rates legal disclosure
    # without playing the SMS scheduling offer message first.
    llm_request.config.hide_tool("play_message_data_rates_disclosure")

  if not callback_context.state.get("played_message_data_rates_legal_disclosure"):
    # Disallow sending appointment link SMS without playing the
    # message and data rates legal disclosure message first.
    llm_request.config.hide_tool("send_appointment_link_sms")

  return None
