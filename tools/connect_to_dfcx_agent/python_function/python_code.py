import random
import re
from typing import Optional


COMPUTING_DEVICES = (
    "computer", "laptop", "desktop", "macbook", "chromebook", "notebook",
    "tablet", "ipad", "surface",
    "printer", "scanner", "fax",
    "hard drive", "external drive", "external storage",
    "copier", "monitor", "pc", "mac", "imac",
    "router", "modem", "keyboard", "mouse", "trackpad",
)

RECLASSIFICATION_INSTRUCTION = (
    '[RECLASSIFICATION REQUIRED] Before this transfer proceeds, carefully '
    're-evaluate the user\'s intent: "{user_query}". '
    'If this intent involves technical assistance, setup, configuration, '
    'troubleshooting, repair, how-to help, connectivity issues, or a service '
    'appointment for a computing device (computer, laptop, desktop, macbook, '
    'chromebook, tablet, iPad, printer, scanner, fax, or external hard drive), '
    'you MUST silently call {{@TOOL: route_computer_troubleshooting_intent}} instead. '
    'you MUST silently call {{@TOOL: connect_to_dfcx_agent}} if the intent is clearly NOT '
    'about technical assistance, setup, troubleshooting, repair, how-to help, '
    'or a service appointment for a computing device (e.g. TVs, phones, '
    'appliances, orders, billing, returns, purchases, policy questions).'
)

def connect_to_dfcx_agent(
    user_query: str,
    is_proactive_routing: bool = False,
) -> Optional[str]:
  """Connects the user to a virtual Dialogflow agent.

  Args:
      user_query (str): A precise, first-person summary of the user's intent (e.g., "I want to...", "I need help with...").
        - MUST include any specific entities mentioned (subscription types, product names, etc.).
        - Rephrase for clarity: Convert fragmented conversation history into a single, coherent statement of intent.
        - DO NOT include conversational filler like "Hello" or "The user said."
        - Example: "I want to buy an iPhone 17 Pro Max."
      is_proactive_routing (bool): Flag indicating if the transfer was triggered by the agent's initial proactive prompt.
        - MUST be set to True only if the transfer is related to the agent's proactive question (e.g. "I see you have an upcoming in-home service appointment. Is that why you're calling?") at the beginning of the conversation.

  Returns:
      Optional[str]: A reclassification instruction when reclassification is enabled
      and a computing-device query is matched; otherwise None.
  """

  if is_proactive_routing:
    context.state["should_connect_to_dfcx_agent"] = True
    # TODO: Remove should_connect_to_dfcx_agent after migration.
    tools.set_next_agent_actions({
        "agent_transfer": {"agent": "DFCX Agent Transfer"},
    })
    context.state["dfcx_params"]["userQuery"] = user_query
    proactive_code = context.state.get("proactive_code")
    if proactive_code == "APT":
      context.state["dfcx_params"]["category"] = "appointments"
    elif proactive_code == "ORDERS":
      context.state["dfcx_params"]["category"] = "orders"
    elif proactive_code == "AUTH":
      context.state["dfcx_params"]["category"] = "membership_auth_fail"
    elif proactive_code == "REPAIR_COMPLETE":
      context.state["dfcx_params"]["category"] = "instore_repair_offer_text"
    elif proactive_code == "REPAIR_IN_PROGRESS":
      context.state["dfcx_params"]["category"] = "instore_repair_status"
    return None

  if _is_reclassification_enabled() and _mentions_computing_device(user_query):
    context.state["enable_fallback_and_reclassification"] = False
    context.state["should_connect_to_dfcx_agent"] = False
    print(
        "CT_RECLASS: Returning reclassification instruction for "
        f"userQuery={user_query}"
    )
    return RECLASSIFICATION_INSTRUCTION.format(user_query=user_query)

  context.state["should_connect_to_dfcx_agent"] = True
  # TODO: Remove should_connect_to_dfcx_agent after migration.
  tools.set_next_agent_actions({
      "agent_transfer": {"agent": "DFCX Agent Transfer"},
  })
  context.state["dfcx_params"]["userQuery"] = user_query
  return None

def _mentions_computing_device(user_query: str) -> bool:
  query_lower = user_query.lower()
  for device in COMPUTING_DEVICES:
    pattern = r"\b{}\b".format(re.escape(device.lower()))
    if re.search(pattern, query_lower):
      return True
  return False

def _is_reclassification_enabled() -> bool:
  init_json = context.state.get("init_json", {})
  return (
      bool(context.state.get("enable_fallback_and_reclassification"))
      and init_json.get("is_reclassification_enabled", "false") == "true"
  )

