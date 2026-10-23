"""Module for checking support entitlement and defining the routing logic."""

# pylint: disable=undefined-variable

OFFER_AGENT_SUPPORT = """1. Let the user know that you can connect them with an agent to discuss their options, and ask them if they would like to be transferred (e.g. "An agent can review available options with you. Would you like to speak with one now?").
2. Wait for the user to respond.
3. Evaluate the user's response:
- If the user responds affirmatively: let the user know you are connecting them for support (e.g. "Okay, let's get you the support you need") and then call {@TOOL: connect_to_computing_service_live_agent}.
- If the user responds negatively: call {@TOOL: call_wrapup}.
- If the user responds ambiguously, seek clarification."""
IN_STORE_APPOINTMENT = """Silently and immediately transition to the `Schedule_InStore_Appointment` subtask"""
REMOTE_TROUBLESHOOTING = """Silently and immediately transition to the `Setup_Remote_Support` subtask"""
ASK_FOR_PROTECTION_PLAN = """Ask the user if they have a Best Buy Protection Plan for the device. e.g. "Do you have a Best Buy Protection Plan for it?
- If the user responds ambiguously, seek clarification.
- If the user responds affirmatively: {offer_support}.
- If the user responds negatively: {no_offer_support}."""


def check_support_entitlement(is_windows_or_mac_os: bool) -> str:
  """Determines the next conversational step based on user eligibility.

  The Agent MUST strictly execute the instructions returned by this tool without
  deviation.

  ### PRE-REQUISITES:
  Before calling this tool, the agent MUST have identified:
  - The `product_type` and called `set_product_info` to store it.
  - The issue `classification` ('software' or 'hardware'), and called either
    `classify_user_issue_as_software` or `classify_user_issue_as_hardware` to
    store it.

  Args:
      is_windows_or_mac_os (bool): Set to True if the device's operating
        system is a variation of Windows or macOS. Otherwise, set to False.

  Returns:
      str: A mandatory instruction set that the agent MUST follow to continue
        the conversation flow.
  """
  membership = context.state.get("membership")
  product_type = context.state.get("product_type")
  issue_type = context.state.get(
      "computer_troubleshooting_issue_classification", "software"
  )
  is_covered_by_protection_plan = context.state.get(
      "protection_plan_status", False
  )
  found_in_purchase_history = context.state.get("item_id") is not None

  if product_type in ("printer", "scanner", "fax"):  # printer
    if membership == "Total" or is_covered_by_protection_plan:
      return _offer_support(issue_type, is_windows_or_mac_os)
    if not found_in_purchase_history:
      return _ask_for_protection_plan(issue_type, is_windows_or_mac_os)
    else:
      return OFFER_AGENT_SUPPORT
  elif product_type in ("iPad", "tablet"):  # tablet
    if issue_type == "software":
      return OFFER_AGENT_SUPPORT
    return IN_STORE_APPOINTMENT
  else:  # computer
    return _offer_support(issue_type, is_windows_or_mac_os)


def _offer_support(issue_type: str, is_windows_or_mac_os: bool) -> str:
  """Determines whether to offer remote help or an in-store appointment."""
  if not is_windows_or_mac_os:
    return IN_STORE_APPOINTMENT

  if issue_type == "software":
    return REMOTE_TROUBLESHOOTING
  else:
    return IN_STORE_APPOINTMENT


def _ask_for_protection_plan(
    issue_type: str, is_windows_or_mac_os: bool
) -> str:
  """Formats the prompt to ask if there is a Best Buy Protection Plan."""
  return ASK_FOR_PROTECTION_PLAN.format(
      offer_support=_offer_support(issue_type, is_windows_or_mac_os),
      no_offer_support=OFFER_AGENT_SUPPORT,
  )
