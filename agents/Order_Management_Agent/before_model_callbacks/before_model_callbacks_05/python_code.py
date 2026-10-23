from typing import Optional


def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
  if (
      llm_request.config
      and llm_request.config.tools
      and llm_request.config.system_instruction
      and llm_request.config.system_instruction.parts
  ):
    current_instruction = llm_request.config.system_instruction.parts[0].text
    for func_decl in llm_request.config.tools[0].function_declarations:
      if func_decl.name not in current_instruction:
        if (
            llm_request.config.excluded_tools is None
            or func_decl.name not in llm_request.config.excluded_tools
        ):
          llm_request.config.hide_tool(func_decl.name)

  return None
