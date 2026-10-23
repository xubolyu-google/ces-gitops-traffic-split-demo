import re

def set_alternative_sms_number(alternative_number: str) -> None:
  """Sets the alternative SMS number to send the schedule a service page link to if provided by the user.

  Args:
      alternative_number (str): The 10-digit US phone number provided by the user. Must be in the format XXXXXXXXXX, 1XXXXXXXXXX, or +1XXXXXXXXXX.

  Returns:
      str: A mandatory instruction set that the agent MUST follow to
            continue the conversation flow.
  """

  # Regex checks for optional +1 or 1 followed by exactly 10 digits
  if not re.match(r"^(\+?1)?\d{10}$", alternative_number):
    return (
      f"1. Tell the user their number doesn't look valid and ask them for a valid one (e.g., 'The phone number {alternative_number} doesn't look valid, can you please provide a valid 10 digit phone number?').\n"
      "2. Wait for the user's response before continuing.\n"
      "3. Call this tool again with the user's updated phone number."
    )

  context.state["alternative_sms_number"] = alternative_number
  return (
    f"1. Ask the user to confirm that they'd like to have the text sent to '{alternative_number}'.\n"
    "2. Wait for the user's response before continuing.\n"
    "3. If the user responds affirmatively, call {@TOOL: " + context.state["send_sms_tool"] + "} with 'use_alternative_number' = True.\n"
    "4. If the user declines, have them provide a new number and call this tool again."
  )
