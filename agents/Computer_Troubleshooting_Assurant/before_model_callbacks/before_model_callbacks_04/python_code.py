def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:

  issue_type = callback_context.state.get(
      "computer_troubleshooting_issue_classification"
  )
  product_type = callback_context.state.get("product_type", "")
  item_id = callback_context.state.get("item_id")

  if issue_type == "software":
    # For software issues, entitlement is determined by
    # check_support_entitlement only. Hide create_and_get_service_context
    # and present_service_path_option to prevent them from being called
    # in the software flow.
    llm_request.config.hide_tool("create_and_get_service_context")
    llm_request.config.hide_tool("present_service_path_option")

  # Printers not found in purchase history skip service context
  if product_type == "printer" and not item_id:
    llm_request.config.hide_tool("create_and_get_service_context")
    llm_request.config.hide_tool("present_service_path_option")

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
    llm_request.config.hide_tool("send_appointment_link_sms")

  return None
