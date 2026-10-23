def play_fallback_sms_scheduling_offer() -> None:
  """Play the fallback one-time text offer for an appointment scheduling link that a user needs to explicitly consent to."""
  context.state["should_play_sms_scheduling_offer"] = True
  context.state["is_proactive_sms_offer"] = False
