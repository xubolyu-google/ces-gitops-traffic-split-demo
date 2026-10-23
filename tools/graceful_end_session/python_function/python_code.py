def graceful_end_session() -> str:
  """End the session with a graceful goodbye message.

  The Agent MUST strictly execute the instructions returned by this tool without
    deviation.

  Returns:
      str: A mandatory instruction set that the agent MUST follow to end
        the conversation flow.
  """
  context.state["should_end_session"] = True
  if not context.state.get("called_set_call_context"):
    # Set call context with queue = "disconnect.nga" on normal exit.
    call_context = context.state["call_context"]
    call_context["queue"] = "disconnect.nga"
    tools.set_call_context({"call_context": call_context})
  return (
      'You MUST say exactly "We appreciate you choosing Best Buy. Have a great'
      ' day." and nothing else. Do NOT add any pleasantries, follow-up'
      ' questions, or summaries (e.g., do NOT say "Is there anything else?").'
  )
