# pylint: disable=missing-function-docstring,missing-class-docstring,missing-module-docstring,invalid-name,undefined-variable,unused-argument,g-short-docstring-punctuation,g-no-space-after-docstring-summary


def classify_user_issue_as_hardware(hardware_status: str) -> None:
  """Classifies the user's issue as a hardware issue for internal reporting
  purposes, along with the status of the user's hardware. This is internal
  metadata. Execution of this tool should be treated as a silent background
  action; do not announce to the user that you are classifying their issue or
  what the classification is.

  Args:
    hardware_status (str): The status of the user's hardware, using best effort
    inference based on details presented in the conversation, defaulting to
    "Unknown" if ambiguous. Valid values:
      - "Broken/Nonfunctional"
      - "Like New"
      - "Normal"
      - "Lost/Stolen"
      - "Damaged"
      - "Unknown"

  Returns:
      None
  """
  context.state["computer_troubleshooting_issue_classification"] = "hardware"
  context.state["hardware_status"] = hardware_status
