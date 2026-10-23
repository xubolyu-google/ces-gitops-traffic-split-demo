def graceful_end_session_order_management() -> None:
  """End the session gracefully with a goodbye message and disconnect the call."""
  if not context.state.get("called_set_call_context"):
    # Set call context with queue = "disconnect.nga" on normal exit.
    call_context = context.state.get("call_context", {})
    call_context["queue"] = "disconnect.nga"
    tools.set_call_context({"call_context": call_context})

  tools.set_next_agent_actions({
      "customized_response": {
          "content": "We appreciate you choosing Best Buy. Have a great day.",
          "disable_barge_in": True,
      },
      "end_session": {"reason": "normal exit"},
  })
  return None
