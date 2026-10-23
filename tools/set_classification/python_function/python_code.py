def set_classification(classification: str) -> None:
  """Sets the classification of the user's computer troubleshooting issue as either hardware or software.

  Args:
      status (str): The classification. Can be either "hardware" or "software".

  Returns:
      None
  """
  context.state["computer_troubleshooting_issue_classification"] = classification
