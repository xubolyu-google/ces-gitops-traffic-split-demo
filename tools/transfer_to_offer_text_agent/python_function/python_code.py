def transfer_to_offer_text_agent() -> None:
  """Transfers the user to the Offer Text agent.

  CRITICAL INSTRUCTION FOR AUDIO TRANSITIONS:
  You MUST call this tool SILENTLY. Do NOT generate any conversational text,
  transitional phrases, or sign-offs (e.g., "Please wait", "I will transfer
  you", "Glad that fixed it") in the same turn that you call this tool.

  The Offer Text Agent is specifically designed to offer a text to be sent to the user , if the user agrees to it.

  Returns:
      None
  """
  # callback will handle the transfer to offer text agent.

  context.state["should_connect_to_offer_text_agent"] = True