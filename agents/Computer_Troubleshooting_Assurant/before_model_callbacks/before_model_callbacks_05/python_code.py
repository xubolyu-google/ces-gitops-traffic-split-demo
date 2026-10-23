FALLBACK_SMS_OFFER = """No problem. More dates, times, and locations are available, but you'll need to view them online. To schedule an appointment, use our Schedule a Service page on BestBuy.com. Could we send you a one-time text message with a link to the Schedule a Service page?"""

PROACTIVE_SMS_OFFER = """To schedule an appointment, use our Schedule a Service page on BestBuy.com. Could we send you a one-time text message with a link to the Schedule a Service page?"""

DATA_RATES_LEGAL_DISCLOSURE = """OK, just so you know, the terms at BestBuy.com/mobile terms apply. Message and data rates may also apply. Can we text you at the number you're calling from?"""

MAIL_IN_REPAIR_SMS = """Ok, the next step happens online at BestBuy.com/selfservice where you can get your request started. Could we send you a one-time text message with a link to the Repair & Tech Services page?"""



def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
  # Popping the value so that this is played exactly once per
  # play_proactive_sms_scheduling_offer or
  # play_fallback_sms_scheduling_offer call. For the edge case
  # where the user has another issue and comes back to
  # troubleshooting, this can be played again via another
  # play_XXX_sms_scheduling_offer call.
  if callback_context.state.pop("should_play_sms_scheduling_offer", False):
    # Unhides the send sms tool in a separate callback so that the agent can now
    # send, but couldn't prematurely send before disclaimer is read.

    # Assign script based on whether user is recognized but has
    # declined to schedule an appointment right now, or is
    # unrecognized and needs to schedule online.
    variables = callback_context.variables
    if variables.get("is_proactive_sms_offer"):
      script = PROACTIVE_SMS_OFFER
    else:
      script = FALLBACK_SMS_OFFER

    callback_context.state["played_sms_scheduling_offer"] = True
    sms_offer = Part.from_customized_response(
        content=script, disable_barge_in=True
    )
    return LlmResponse.from_parts(parts=[sms_offer])

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

  return_exchange_phrase = callback_context.state.pop("should_play_return_exchange_option", None)
  if return_exchange_phrase:
    # Force the exact phrase via customized response so the LLM cannot rephrase it.
    return_exchange_option = Part.from_customized_response(
        content=return_exchange_phrase, disable_barge_in=False
    )
    return LlmResponse.from_parts(parts=[return_exchange_option])

  if callback_context.state.pop("should_play_sms_mail_in_repair", False):
    # Unhides the send sms tool in a separate callback so that the agent can now
    # send, but couldn't prematurely send before disclaimer is read.
    callback_context.state["played_should_play_sms_mail_in_repair"] = True
    mail_in_repair_sms = Part.from_customized_response(
        content=MAIL_IN_REPAIR_SMS, disable_barge_in=True
    )
    return LlmResponse.from_parts(parts=[mail_in_repair_sms])