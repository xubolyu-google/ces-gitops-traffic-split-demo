
DATA_RATES_LEGAL_DISCLOSURE = """OK, just so you know, the terms at BestBuy.com/mobile terms apply. Message and data rates may also apply. Can we text you at the number you're calling from?"""

def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
  # Popping the value so that this is played exactly once per
  # play_message_data_rates_disclosure call. For the edge case where the user has another
  # issue and comes back to troubleshooting, this can be played again via
  # another play_message_data_rates_disclosure call.
  if callback_context.state.pop("should_play_message_data_rates_legal_disclosure", False):
    # Unhides the send sms tool in a separate callback so that the agent can now
    # send, but couldn't prematurely send before disclaimer is read.
    callback_context.state["played_message_data_rates_legal_disclosure"] = True
    legal_disclosure = Part.from_customized_response(
        content=DATA_RATES_LEGAL_DISCLOSURE, disable_barge_in=True
    )
    return LlmResponse.from_parts(parts=[legal_disclosure])