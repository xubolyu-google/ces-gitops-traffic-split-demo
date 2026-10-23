import base64
import json as json_lib
import re
from typing import Iterator, Optional


_HOLD_MESSAGES = [
    "Please hold on for a moment while I finish setting things up for you.",
    "I'm still working on it, just a moment.",
    "Sorry, it's taking a little longer than expected. Bear with me.",
    "Almost there, thank you for your patience.",
    "Still setting things up on my end. One more moment please.",
]


def _get_hold_message(count: int) -> str:
  """Return a varied hold message based on the poll count."""
  idx = min(count - 1, len(_HOLD_MESSAGES) - 1)
  return _HOLD_MESSAGES[idx]


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

def _is_waiting_for_lmi(callback_context: CallbackContext) -> bool:
  return (
      callback_context.state.get("lmi_session_created")
      and not callback_context.state.get("lmi_session_resolved")
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

    # If an LMI flow was initiated and not yet resolved, poll LMI and block until resolved.
    was_waiting_for_lmi = _is_waiting_for_lmi(callback_context)
    if was_waiting_for_lmi:
      try:
        data = tools.check_lmi_status({}).json()["result"]
        status = "UNKNOWN"
        session_id = ""

        print(f"[LMI poll] data={data}")
        status = data["Status"]
        session_id = data["ID"]

        callback_context.state["lmi_status"] = status
        print(f"[LMI poll] status={status} id={session_id}")

        if status == "SessionCreated":
          callback_context.state["lmi_session_id"] = session_id
          callback_context.state["lmi_session_resolved"] = True
        elif status == "SessionNotCreated":
          callback_context.state["lmi_session_resolved"] = True
        else:
          just_a_moment_count = int(callback_context.state.get("just_a_moment_count", 0))
          if just_a_moment_count >= 5:
            print(f"[LMI poll] 'Just a moment' count exceeded 5 — treating as SessionNotCreated.")
            callback_context.state["lmi_session_resolved"] = True
          else:
            callback_context.state["just_a_moment_count"] = just_a_moment_count + 1
            return LlmResponse.from_parts(parts=[Part.from_text(_get_hold_message(just_a_moment_count + 1))])
      except Exception as e:
        print(f"ERROR: LMI polling failed: {e!r}")
        just_a_moment_count = int(callback_context.state.get("just_a_moment_count", 0))
        if just_a_moment_count >= 5:
          print(f"[LMI poll] 'Just a moment' count exceeded 5 — treating as SessionNotCreated.")
          callback_context.state["lmi_session_resolved"] = True
        else:
          callback_context.state["just_a_moment_count"] = just_a_moment_count + 1
          return LlmResponse.from_parts(parts=[Part.from_text(_get_hold_message(just_a_moment_count + 1))])

    # If LMI is resolved and a deferred transfer was requested, perform the handoff once.
    try:
      if (
          callback_context.state.get("lmi_session_resolved")
          and not callback_context.state.get("transfer_initiated")
      ):
        print("Deferred transfer requested and LMI resolved — initiating transfer.")
        try:
          tools.connect_to_computing_service_live_agent({
              "conversation_summary": callback_context.state.get("conversation_summary", "")
          })
          callback_context.state["transfer_initiated"] = True
        except Exception as e:
          print(f"ERROR: deferred connect_to_computing_service_live_agent failed: {e!r}")
    except Exception as e:
      print(f"Error handling deferred transfer: {e!r}")

    # No input counter should not be updated while waiting for LMI — silence is expected during that flow.
    if not was_waiting_for_lmi:
      no_input_counter = callback_context.variables.get("no_input_counter", 0) + 1
      callback_context.variables["no_input_counter"] = no_input_counter
    else:
      return None
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