from typing import Optional

def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
  if not callback_context.state.get("orders_by_id"):
    llm_request.config.hide_tool("set_order_id")

  if not callback_context.state.get("order_id"):
    llm_request.config.hide_tool("get_order_details")
    llm_request.config.hide_tool("check_order_actionability")
  return None
