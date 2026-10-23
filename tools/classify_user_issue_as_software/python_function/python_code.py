# pylint: disable=missing-function-docstring,missing-class-docstring,missing-module-docstring,invalid-name,undefined-variable,unused-argument,g-short-docstring-punctuation,g-no-space-after-docstring-summary


def classify_user_issue_as_software() -> None:
  """Classifies the user's issue as a software issue for internal reporting
  purposes. This is internal metadata. Execution of this tool should be treated
  as a silent background action; do not announce to the user that you are
  classifying their issue or what the classification is.

  Returns:
      None
  """
  context.state["computer_troubleshooting_issue_classification"] = "software"
