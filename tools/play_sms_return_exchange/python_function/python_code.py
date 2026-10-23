def play_sms_return_exchange() -> None:
  """Play the fallback one-time text offer for a return or exchange that a user needs to explicitly consent to."""
  context.state["should_play_sms_return_exchange"] = True
 
