SLOW_TOOL_MESSAGE = {
    "check_appointment_slots": (
        "Please bear with me for just a moment while I check our system for the"
        " available time slots."
    ),
    "create_appointment": (
        "Just a second while I secure that time slot for you."
    ),
    "create_and_get_service_context": (
      "Please bear with me for just a moment while I find the right support for you."
    )
}


def after_model_callback(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
  # Track lmi_sop usage so check_lmi_session_status knows setup instructions were delivered.
  for part in llm_response.content.parts:
    if part.has_function_call("lmi_sop"):
      callback_context.state["lmi_sop_called"] = True
      break

  # Do not try to generate a response if there is already a response.
  if any(p.text_or_transcript() for p in llm_response.content.parts):
    return None

  for part in llm_response.content.parts:
    for tool, message in SLOW_TOOL_MESSAGE.items():
      if part.has_function_call(tool):
        return LlmResponse.from_parts(
            parts=[Part.from_text(text=message)] + llm_response.content.parts
        )
  return None
