"""Silent transfer to Graceful Signoff Agent.

Rule: User MUST NEVER hear "Graceful Signoff Agent" or transfer announcement.
Callback-driven to prevent model hallucination (e.g., "I'll transfer you...").
See: Computer_Troubleshooting_Assurant/instruction.txt constraint #9.
"""

# pylint: disable=undefined-variable
from typing import Optional


def after_model_callback(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
  """Execute silent transfer to Graceful Signoff Agent."""
  if callback_context.state.get("should_transfer_to_graceful_signoff"):
    callback_context.state["should_transfer_to_graceful_signoff"] = False
    return LlmResponse.from_parts(
        parts=[Part.from_agent_transfer(agent="Graceful Signoff Agent")]
    )
  return None
