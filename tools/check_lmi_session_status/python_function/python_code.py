def check_lmi_session_status() -> str:
  """Sets the lmi_session_created flag to begin polling for the LMI session.

  This tool must only be called AFTER the agent has retrieved and walked the
  customer through the LMI setup instructions via the lmi_sop tool. Calling
  this tool prematurely (before lmi_sop) will skip the setup steps.
  """
  if not context.state.get("lmi_sop_called"):
    print("[check_lmi_session_status] Skipped: lmi_sop has not been called yet.")
    return "lmi_sop not called"

  context.state["lmi_session_created"] = True
  return "lmi_session_created flag set"
