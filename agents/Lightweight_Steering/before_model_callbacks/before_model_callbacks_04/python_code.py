import base64
import json as json_lib
import re
from typing import Iterator, Optional


def is_user_inactive(contents: List[Content]) -> bool:
  """Check if the user is inactive.

  The input signal for no user activity comes in the following format:

  <context>no user activity detected for X seconds.</context>

  This method will grab the recent list of texts from content and check for the
  existence of the 'no user activity' statement.

  Args:
    all_text (List[str]): the list of contents to check.

  Returns:
    True if the most recent message contains the no input signal, False
    otherwise.
  """
  silence_pattern = (
      r"<context>no user activity detected for \d+ seconds\.</context>"
  )
  return len(contents) > 1 and any(
      re.search(silence_pattern, p.text, re.IGNORECASE)
      for p in contents[-1].parts
      if p.text
  )


def get_reversed_agent_messages(contents: List[Content]) -> Iterator[str]:
  for content in reversed(contents):
    # LLM generated message maybe span multiple parts (e.g. ["How can ",
    # "I help you?"]), join them together.
    texts = []
    for part in content.parts:
      if content.role == "model" and part.text is not None:
        texts.append(part.text)
    if texts:
      yield "".join(texts)

    # Handle customized_response messages.
    for part in reversed(content.parts):
      if (
          part.inline_data
          and part.inline_data.mime_type == "application/json+agentResponse"
      ):
        customized_response = json_lib.loads(
            base64.b64decode(part.inline_data.data).decode("utf-8")
        )
        yield customized_response["content"]


def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
  try:
    if not is_user_inactive(llm_request.contents):
      callback_context.variables["no_input_counter"] = 0
      return None

    no_input_counter = callback_context.variables.get("no_input_counter", 0) + 1
    callback_context.variables["no_input_counter"] = no_input_counter
    print(f"no input count: {no_input_counter}")

    if no_input_counter < 3:
      reversed_agent_messages = get_reversed_agent_messages(
          llm_request.contents
      )

      if no_input_counter == 1:
        latest_agent_response = next(reversed_agent_messages)
        agent_response = (
            f"Sorry, I didn't hear anything. {latest_agent_response}"
        )
      else:
        next(reversed_agent_messages)
        latest_agent_response = next(reversed_agent_messages)
        agent_response = f"I still can't hear you. {latest_agent_response}"

      return LlmResponse.from_parts(parts=[Part.from_text(agent_response)])
    else:
      return LlmResponse.from_parts(
          parts=[
            Part.from_text(
                "Sorry about that. You can try calling again later. We"
                " appreciate you choosing Best Buy. Have a great day."
            ),
            Part.from_end_session(reason="No Input Limit Exceeded"),
          ]
      )
  except Exception as e:
    print("Error in no-input maxout callback: {}".format(e))