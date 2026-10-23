def call_wrapup() -> None:
  """Transfers the user to the Graceful Signoff agent.

  CRITICAL INSTRUCTION FOR AUDIO TRANSITIONS:
  You MUST call this tool SILENTLY. Do NOT generate any conversational text,
  transitional phrases, or sign-offs (e.g., "Please wait", "I will transfer
  you", "Glad that fixed it") in the same turn that you call this tool.

  The Graceful Signoff Agent is specifically designed to speak the final
  transitional phrases and sign-offs to the user. Generating text before
  calling this tool will cause the user to hear duplicate, jarring audio.
  Only the Graceful Signoff Agent should speak during this transition.

  Returns:
      None
  """

  context.state["should_transfer_to_graceful_signoff"] = True
