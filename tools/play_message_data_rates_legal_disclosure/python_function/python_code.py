def play_message_data_rates_legal_disclosure() -> None:
  """Play the mandatory text message and date rates legal disclosure that a user needs to explicitly consent to before you can send an SMS for appointment booking."""

  # Makes sure the one-time-text legal disclosure is played and pops it so that for the
  # edge case where the user has another issue and comes back to
  # troubleshooting, we will require legal disclosure to be played again.
  played_sms_scheduling = context.state.pop("played_sms_scheduling_offer", False)
  played_sms_mail_in_repair = context.state.pop(
      "played_should_play_sms_mail_in_repair", False
  )
  played_sms_return_exchange = context.state.pop(
      "played_should_play_sms_return_exchange", False
  )

  if not (
      played_sms_scheduling
      or played_sms_mail_in_repair
      or played_sms_return_exchange
  ):
    return (
        "You MUST call {@TOOL: play_proactive_sms_scheduling_offer}"
        " or {@TOOL: play_fallback_sms_scheduling_offer}"
        " or {@TOOL: play_sms_mail_in_repair} and obtain"
        " user consent before calling this tool."
    )

  context.state["should_play_message_data_rates_legal_disclosure"] = True
