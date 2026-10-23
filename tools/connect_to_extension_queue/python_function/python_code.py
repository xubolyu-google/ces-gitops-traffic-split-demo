"""Implementation of the connect_to_extension_queue tool."""

# pylint: disable=undefined-variable,g-wrong-blank-lines


def connect_to_extension_queue() -> str | None:
  """Connects the user to the extension queue when the user presses # or requests to reach an extension.

  Returns:
    None: The transfer to the extension queue was successfully initiated.
      Proceed normally.
    str: The transfer failed (national line). If a string is returned, you MUST
      immediately stop your current logic and strictly execute the returned
      instructions word-for-word to recover from the failure.
  """

  store_id = context.state.get("store_id")

  if store_id:
    # Implies regional line. Extension transfer allowed.
    context.variables["should_connect_to_twilio_queue_directly"] = True
    # TODO: Remove should_connect_to_twilio_queue_directly after migration.
    tools.set_next_agent_actions({
        "end_session": {"reason": "Transfer to Twilio queue"},
    })
    call_context = context.state.get("call_context", {})
    call_context["queue"] = "RTL.EXT.______.EN.VCE.ALL"
    # callback will handle the transfer to Twilio (i.e. end the session).
    tools.set_call_context({"call_context": call_context})
    return None
  else:
    # Implies national line. Extension transfer forbidden.
    return (
        f"1. You must say exactly: \"It seems you're trying to reach an"
        f" extension,"
        " but you've dialed Best Buy national. If you wish to reach a specific"
        " extension, please hang up and dial the number for the retail store"
        " you wish to reach. Is there anything else I can help you with"
        ' instead?"\n'
        f"2. Wait for the user's response, then strictly follow these rules:\n"
        f'   - If the user responds negatively: Say "We appreciate you choosing'
        f' Best Buy. Have a great day." and call {{@TOOL: end_session}} in the'
        f" same turn.\n"
        f"   - Else: Continue with the instruction flow from where you left"
        f" off, repeating your previous utterance if necessary (i.e. you didn't"
        f" capture a response and need one to proceed effectively).\n"
    )
