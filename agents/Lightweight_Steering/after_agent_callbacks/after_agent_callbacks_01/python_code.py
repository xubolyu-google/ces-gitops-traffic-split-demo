# pylint: disable=missing-function-docstring,missing-class-docstring,missing-module-docstring,invalid-name,undefined-variable


def after_agent_callback(
    callback_context: CallbackContext,
) -> Optional[Content]:
  callback_context.state['llm_steps'] = 0
