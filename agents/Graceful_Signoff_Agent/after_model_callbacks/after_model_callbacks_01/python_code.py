def after_model_callback(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
  if callback_context.state.get("should_end_session"):
    return LlmResponse.from_parts(
        parts=[Part.from_end_session(reason="normal exit")]
    )
