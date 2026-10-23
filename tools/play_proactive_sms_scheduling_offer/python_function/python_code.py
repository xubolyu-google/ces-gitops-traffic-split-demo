def play_proactive_sms_scheduling_offer() -> None:
  """Play the proactive one-time text offer for an appointment scheduling link that a user needs to explicitly consent to."""
  context.state["should_play_sms_scheduling_offer"] = True
  context.state["is_proactive_sms_offer"] = True
