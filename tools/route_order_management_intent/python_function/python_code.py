def route_order_management_intent(user_query: str) -> None:
  """Handles routing of an order management intent.

  Args:
      user_query (str): a summary of the user's intent.

  Returns:
      None
  """
  context.state["user_query"] = user_query
  context.state["should_connect_to_order_management_agent"] = True
