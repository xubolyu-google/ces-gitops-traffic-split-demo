def play_sms_mail_in_repair() -> None:
  """Play the fallback one-time text offer for an mail in repair that a user needs to explicitly consent to."""
  context.state["should_play_sms_mail_in_repair"] = True
