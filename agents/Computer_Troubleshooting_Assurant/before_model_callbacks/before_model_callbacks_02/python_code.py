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

  if callback_context.variables.get("should_connect_to_twilio_queue_directly"):
    return LlmResponse.from_parts(
        parts=[Part.from_end_session(reason="Transfer to Twilio queue")]
    )

  # Hide end_session tool from the model since end_session can only be
  # called via callback for this agent.
  llm_request.config.hide_tool("end_session")

  if callback_context.variables.get("should_connect_to_dfcx_agent"):
    return LlmResponse.from_parts(
        parts=[Part.from_agent_transfer(agent="DFCX Agent Transfer")]
    )

  # Hide transfer_to_agent from the model since transfers must only be invoked
  # via callback for this agent to ensure reliability and pre-requisite tools
  # are called in the same turn.
  llm_request.config.hide_tool("transfer_to_agent")

  return None
