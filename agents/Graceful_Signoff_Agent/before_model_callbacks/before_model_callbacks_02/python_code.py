def before_model_callback(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
  if callback_context.variables.get(
      "should_connect_to_twilio_queue_with_response"
  ):
    return LlmResponse.from_parts(
        parts=[
            Part.from_customized_response(
                content="Ok, let me connect you with an agent.",
                disable_barge_in=True,
            ),
            Part.from_end_session(reason="Transfer to Twilio queue"),
        ]
    )
  if not callback_context.variables.get("should_end_session"):
    # Hide end_session tool from the model since end_session should only be
    # called via after_model_callback.
    llm_request.config.hide_tool("end_session")

  if callback_context.variables.get("should_connect_to_twilio_queue_directly"):
    return LlmResponse.from_parts(
        parts=[Part.from_end_session(reason="Transfer to Twilio queue")]
    )

  if callback_context.variables.get("should_connect_to_dfcx_agent"):
    return LlmResponse.from_parts(
        parts=[Part.from_agent_transfer(agent="DFCX Agent Transfer")]
    )

  return None
