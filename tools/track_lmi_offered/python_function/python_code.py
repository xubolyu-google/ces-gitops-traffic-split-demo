def track_lmi_offered() -> str:
  """Tracks that the LMI remote support option was presented to the customer.

  Sets the lmi_offered flag in session state so that downstream analytics
  can determine whether the customer was offered LMI regardless of whether
  they accepted or declined.

  Returns:
      str: Confirmation that the flag was set.
  """
  context.state["lmi_offered"] = True
  return "tracked"
