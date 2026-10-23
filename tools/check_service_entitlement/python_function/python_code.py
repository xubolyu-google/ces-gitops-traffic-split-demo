DEFLECT_TO_MANUFACTURER = """Silently and immediately call the {@TOOL: call_wrapup} tool."""

IN_STORE_APPOINTMENT = """Silently and immediately transition to the `Gather_Appointment_Preferences` step of the `Schedule_InStore_Appointment` subtask. The appointment offer was already presented to the user."""

REMOTE_TROUBLESHOOTING = """Silently and immediately transition to the `Guided_Remote_Support_Software_Download` step of the `Setup_Remote_Support` subtask. The remote support offer was already presented and accepted."""

RETURN_EXCHANGE = """Silently and immediately call the {@TOOL: transfer_to_offer_text_agent} tool."""
AGENT = """Silently and immediately call the {@TOOL: connect_to_computing_service_live_agent} tool"""

ASSURANT_MAIL_IN = """
      1. Say exactly: "We can provide a prepaid label to send your device to our Geek Squad Service Center. They'll inspect it, contact you with service options, and you can track the repair online. Service fees may apply. Would you like to get started?"
      2. Wait for the user to answer before continuing.
        2a. If the user responds affirmatively, proceed to 3.
        2b. If the user declines, silently and immediately transition to the `Schedule_InStore_Appointment` subtask.
      3. You MUST immediately and silently call {@TOOL: play_sms_mail_in_repair}.
      4. Wait for the user to answer before continuing.
      5. Analyze the user's response:
        5a. If the user responds affirmatively, immediately call the {@TOOL: transfer_to_offer_text_agent} tool.
        5b. If the user declines, silently and immediately call the {@TOOL: call_wrapup} tool.
      """

def check_service_entitlement(path_type: str, link: str = "") -> str:
  """Determines the next conversational step based on user eligibility.

  The Agent MUST strictly execute the instructions returned by this tool without
  deviation.

  Args:
      path_type: The service path type string, e.g. "Dotcom_SelfService_ServiceTriage".
      link: The URL/link associated with the selected service path option.

  Returns:
      str: A mandatory instruction set that the agent MUST follow to continue
        the conversation flow.
  """
  # Store the service context details
  context.state["page_link"] = link
  context.state["path_type"] = path_type

  init_json = context.state.get("init_json", {})
  is_mail_in_enabled = str(init_json.get("mail_in_enabled", False)).lower() == "true"


  if path_type == "Dotcom_SelfService_RepairDeflect":
    context.state["should_transfer_to_graceful_signoff"] = True
    return DEFLECT_TO_MANUFACTURER
  elif path_type == "Dotcom_SelfService_ReturnExchange":
    context.state["page_title"] = "Returns and Exchanges"
    context.state["sms_event_id"] = "IVR_AS_RepairRequest"
    context.state["played_should_play_sms_return_exchange"] = True
    return RETURN_EXCHANGE
  elif path_type == "Dotcom_SelfService_RemoteSupport":
    return REMOTE_TROUBLESHOOTING
  elif path_type == "Dotcom_SelfService_RepairCreate_InStoreAppointment":
    return IN_STORE_APPOINTMENT
  elif path_type == "Dotcom_SelfService_ServiceTriage":
    if is_mail_in_enabled:
      context.state["page_title"] = "Repair & Tech Services"
      context.state["sms_event_id"] = "IVR_AS_RepairRequest"
      return ASSURANT_MAIL_IN
    else:
      return IN_STORE_APPOINTMENT
  else:
    # Log what fell through
    print(f"DEBUG: No match found for path_type: '{path_type}', defaulting to AGENT")
    return AGENT


