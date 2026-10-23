"""After model callback logic for Graceful Signoff transfer."""

# pylint: disable=undefined-variable
from typing import Optional


def after_model_callback(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
  if callback_context.state.get("should_connect_to_offer_text_agent"):
    callback_context.state["should_connect_to_offer_text_agent"] = False
    return LlmResponse.from_parts(
        parts=[Part.from_agent_transfer(agent="Offer Text Agent")]
    )
  return None
