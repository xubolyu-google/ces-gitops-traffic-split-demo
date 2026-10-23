def before_model_callback(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
  if callback_context.variables.get("should_connect_to_twilio_queue_directly"):
    return LlmResponse.from_parts(
        parts=[Part.from_end_session(reason="Transfer to Twilio queue")]
    )

  # Hide end_session tool from the model since end_session can only be
  # called via callback for this agent.
  llm_request.config.hide_tool("end_session")
  if callback_context.variables.get("should_connect_to_dfcx_agent"):
    return LlmResponse.from_parts(
        parts=[Part.from_agent_transfer(agent="DFCX Agent Transfer")]
    )

  if callback_context.state.get("should_connect_to_computer_troubleshooting_agent"):
    # Because the conversation can get routed back to steering on subsequent issues,
    # need to reset to prevent infinite loops.
    callback_context.state["should_connect_to_computer_troubleshooting_agent"] = False
    return LlmResponse.from_parts(
        parts=[Part.from_agent_transfer(agent="Computer Troubleshooting Agent")]
    )

  if callback_context.state.get("should_connect_to_computer_troubleshooting_assurant_agent"):
    # Because the conversation can get routed back to steering on subsequent issues,
    # need to reset to prevent infinite loops.
    callback_context.state["should_connect_to_computer_troubleshooting_assurant_agent"] = False
    return LlmResponse.from_parts(
        parts=[Part.from_agent_transfer(agent="Computer Troubleshooting Assurant")]
    )

  if callback_context.state.get("should_connect_to_order_management_agent"):
    callback_context.state["should_connect_to_order_management_agent"] = False
    return LlmResponse.from_parts(
        parts=[Part.from_agent_transfer(agent="Order Management Agent")]
    )
  
  import re
  llm_request.config.hide_tool("transfer_to_agent")
  
  pattern = r"You have a list of other agents to transfer to:.*?the only available agents for `transfer_to_agent` function are .*?\."
  
  instruction = llm_request.config.system_instruction.parts[0].text
  cleaned_instruction, replaced = re.subn(pattern, "", instruction, flags=re.DOTALL)
  if not replaced:
    print("transfer_to_agent instruction is not replaced!")
  llm_request.config.system_instruction.parts[0].text= cleaned_instruction
  
  return None