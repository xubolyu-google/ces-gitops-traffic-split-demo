def connect_to_spanish_agent() -> str | None:
  """
  Connects the user to a spanish speaking agent when the user requests to speak Spanish (e.g. by saying "Spanish" or "Espanol")

  Returns:
    None: The transfer to the Spanish agent was successfully initiated. Proceed normally.
    str: The transfer failed (regional line). If a string is returned, you MUST 
          immediately stop your current logic and strictly execute the returned instructions
          word-for-word to recover from the failure.
  """
  store_id = context.state.get("store_id")

  if not store_id:
    # Implies national line. Spanish transfer allowed.
    # callback will handle the transfer to dfcx.
    context.variables["should_connect_to_dfcx_agent"] = True
    # TODO: Remove should_connect_to_dfcx_agent after migration.
    tools.set_next_agent_actions({
        "agent_transfer": {"agent": "DFCX Agent Transfer"},
    })
    tools.connect_to_dfcx_agent({"user_query": "espanol"})
    return None
  else:
    # Implies regional line. Spanish transfer forbidden.
    store_name = context.state.get("store_name", "")

    # Return strict instructions for the agent to perform in the event of a regional line.
    return (
        f"1. You must say exactly: \"It seems you're looking for assistance in Spanish, but you've dialed the regional number for Best Buy {store_name}. If you need help in Spanish, please call back at the Best Buy national number and we can connect you with a Spanish agent. Do you wish to continue in English?\"\n"
        f"2. Wait for the user's response, then strictly follow these rules:\n"
        f"   - If the user responds affirmatively: Continue with the instruction flow from where you left off, repeating your previous utterance if necessary (i.e. you didn't capture a response and need one to proceed effectively).\n"
        f"   - If the user responds negatively: Say \"We appreciate you choosing Best Buy. Have a great day.\" and call {{@TOOL: end_session}} in the same turn."
    )
