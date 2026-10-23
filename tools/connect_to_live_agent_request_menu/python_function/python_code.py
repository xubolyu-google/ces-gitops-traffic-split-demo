def connect_to_live_agent_request_menu() -> None:
  """Connects the user to the live agent request menu which will prompt and route the user to the desired live agent queue.

  Returns:
      None
  """
  # callback will handle the transfer to dfcx.
  context.variables["should_connect_to_dfcx_agent"] = True
  # TODO: Remove should_connect_to_dfcx_agent after migration.
  tools.set_next_agent_actions({
      "agent_transfer": {"agent": "DFCX Agent Transfer"},
  })
  context.state["dfcx_params"]["userQuery"] = "live agent transfer"
