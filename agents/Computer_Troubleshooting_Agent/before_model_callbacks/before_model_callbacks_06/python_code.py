_HOLD_MESSAGES = [
    "Please hold on for a moment while I finish setting things up for you.",
    "I'm still working on it, just a moment.",
    "Sorry, it's taking a little longer than expected. Bear with me.",
    "Almost there, thank you for your patience.",
    "Still setting things up on my end. One more moment please.",
]


def _get_hold_message(count: int) -> str:
  """Return a varied hold message based on the poll count."""
  idx = min(count - 1, len(_HOLD_MESSAGES) - 1)
  return _HOLD_MESSAGES[idx]


def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
  try:
    # If an LMI flow was initiated and not yet resolved, poll LMI and block until resolved.
    if callback_context.state.get("lmi_session_created") and not callback_context.state.get("lmi_session_resolved"):
      try:
        data = tools.check_lmi_status({}).json()["result"]
        status = "UNKNOWN"
        session_id = ""

        # Simple extraction per your request
        print(f"[LMI poll] data={data}")
        # direct extraction of Status (may raise if key missing; guard below)
        status = data["Status"] 
        session_id =  data["ID"] 

        callback_context.state["lmi_status"] = status
        print(f"[LMI poll] status={status} id={session_id}")

        if status == "SessionCreated":
          callback_context.state["lmi_session_id"] = session_id
          callback_context.state["lmi_session_resolved"] = True
          # allow LLM to continue this turn
        elif status == "SessionNotCreated":
          callback_context.state["lmi_session_resolved"] = True
          # allow LLM to continue this turn
        else:
          # Any other status -> block the LLM this turn and keep polling next turns.
          just_a_moment_count = int(callback_context.state.get("just_a_moment_count", 0))
          if just_a_moment_count >= 5:
            print(f"[LMI poll] 'Just a moment' count exceeded 5 — treating as SessionNotCreated.")
            callback_context.state["lmi_session_resolved"] = True
          else:
            callback_context.state["just_a_moment_count"] = just_a_moment_count + 1
            return LlmResponse.from_parts(parts=[Part.from_text(_get_hold_message(just_a_moment_count + 1))])
      except Exception as e:
        print(f"ERROR: LMI polling failed: {e!r}")
        # On polling error, block this turn and retry next turn.
        just_a_moment_count = int(callback_context.state.get("just_a_moment_count", 0))
        if just_a_moment_count >= 5:
          print(f"[LMI poll] 'Just a moment' count exceeded 5 — treating as SessionNotCreated.")
          callback_context.state["lmi_session_resolved"] = True
        else:
          callback_context.state["just_a_moment_count"] = just_a_moment_count + 1
          return LlmResponse.from_parts(parts=[Part.from_text(_get_hold_message(just_a_moment_count + 1))])

    # If LMI is resolved and a deferred transfer was requested, perform the handoff once.
    try:
      if (
          callback_context.state.get("lmi_session_resolved")
          and not callback_context.state.get("transfer_initiated")
      ):
        print("Deferred transfer requested and LMI resolved — initiating transfer.")
        try:
          # Call the tool with the expected dict payload (silent, deterministic)
          tools.connect_to_computing_service_live_agent({
              "conversation_summary": callback_context.state.get("conversation_summary", "")
          })
          callback_context.state["transfer_initiated"] = True
        except Exception as e:
          print(f"ERROR: deferred connect_to_computing_service_live_agent failed: {e!r}")
    except Exception as e:
      print(f"Error handling deferred transfer: {e!r}")
  except Exception as e:
    print(f"Error in before_model_callback: {e!r}")
    return None    
      
