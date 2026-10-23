from typing import Optional


def before_agent_callback(
    callback_context: CallbackContext,
) -> Optional[Content]:
  callback_context.state["enable_fallback_and_reclassification"] = False

  # Reset next_agent_actions
  # TODO: Remove this after other agents migrate to use next_agent_actions.
  callback_context.state.pop("next_agent_actions", None)
  
  callback_context.state["send_sms_tool"] = "send_sms"

  return None