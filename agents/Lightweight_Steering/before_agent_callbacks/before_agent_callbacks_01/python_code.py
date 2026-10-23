def before_agent_callback(
    callback_context: CallbackContext,
) -> Optional[Content]:
  callback_context.state["enable_fallback_and_reclassification"] = True
  return None