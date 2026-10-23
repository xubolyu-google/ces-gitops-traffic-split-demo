# pylint: disable=undefined-variable
import base64
import json
from typing import Optional


def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
  """If next_agent_actions is set, play the specified agent response or perform the specified actions (i.e. agent transfer, end session, tool calls)."""
  print(f"DEBUG: llm_request {llm_request}")
  actions = callback_context.state.pop("next_agent_actions", None)
  if not actions:
    return None

  parts = []
  if response := actions.get("customized_response"):
    print(f"DEBUG: playing response: {response}")
    # Play the agent response.
    parts.append(Part.from_customized_response(**response))

  if payload := actions.get("custom_payload"):
    payload_string = json.dumps(payload)
    print(f"DEBUG: returning custom payload: {payload_string}")
    parts.append(
        Part(
            inline_data=ces_internal.Blob(
                data=base64.b64encode(payload_string.encode("utf-8")),
                mime_type="application/json",
            )
        )
    )

  nested_actions = None
  if function_calls := actions.get("function_calls"):
    for function_call in function_calls:
      print(f"DEBUG: calling tool {function_call}")
      if function_call.get("name") == "set_next_agent_actions":
        nested_actions = function_call.get("args")
      else:
        parts.append(Part.from_function_call(**function_call))

  if transfer := actions.get("agent_transfer"):
    print(f"DEBUG: transfer to {transfer}")
    parts.append(Part.from_agent_transfer(**transfer))

  if end_session := actions.get("end_session"):
    print(f"DEBUG: ending session: {end_session}")
    parts.append(Part.from_end_session(**end_session))

  response = LlmResponse.from_parts(parts=parts)
  if nested_actions:
    # Run set_next_agent_actions directly within the callback so
    # that it does not pollute the historical context.
    callback_context.state["next_agent_actions"] = nested_actions
    response.partial = True  # Forces another turn.

  return response
