def set_hardware_status(status: str) -> None:
  """Sets the hardware status context variable to separate triage from detailed classification.

  This function allows the agent to defer the specific hardware status classification
  until after the initial triage is complete.

  Args:
      status (str): The specific status of the hardware.
          Valid values:
          - "Broken/Nonfunctional"
          - "Unknown"
          - "Like New"
          - "Normal"
          - "Lost/Stolen"
          - "Damaged"

  Returns:
      None
  """
  context.state["hardware_status"] = status
  print(f"INFO: Hardware status set to: {status}")
