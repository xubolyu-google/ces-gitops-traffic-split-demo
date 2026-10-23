# pylint: disable=missing-function-docstring,missing-class-docstring,missing-module-docstring,invalid-name,undefined-variable
from typing import Optional


def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
  steps = callback_context.state['llm_steps'] = (
      int(callback_context.state.get('llm_steps', 0)) + 1
  )
  if steps == 10:
    return LlmResponse.from_parts([
        Part.from_text(
            text=(
                "Hmm, I'm having trouble with that. Do you want me to try again"
                ' or speak to a live agent?'
            )
        )
    ])
