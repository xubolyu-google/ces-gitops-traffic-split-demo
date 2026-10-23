def set_user_problem(user_problem: str) -> None:
  """Records a summary of the user's problem incorporating context and clarifications gathered across the entire conversation.

  Args:
    user_problem (str): a comprehensive summary of the user's problem.

  Returns:
      None
  """
  context.state["user_problem"] = user_problem
