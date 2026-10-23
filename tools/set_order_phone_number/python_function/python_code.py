def set_order_phone_number(phone_number: str) -> None:
  """Sets the order phone number for looking up orders.

  Args:
      phone_number (str): The 10-digit US phone number provided by the user. Must be in the format XXXXXXXXXX, 1XXXXXXXXXX, or +1XXXXXXXXXX.

  Returns:
      None
  """
  context.state["order_phone_number"] = phone_number
  print(f"INFO: Set order_phone_number to {phone_number}")
