from typing import Any


def set_order_intent(intent: str) -> dict[str, Any]:
  """Updates the static variable order_management_subtasks_instruction based on user intent.

  You MUST call this tool immediately upon transfer to the Order Management Agent to populate the correct instruction flow.

  Possible values for intent and their explanations:
    - "check_status": Use when the customer wants to check the status or tracking of an existing order.
    - "cancel": Use when the customer wants to cancel an order, an appointment, or specific items within an order.
    - "modify": Use when the customer wants to modify order details, such as changing shipping speed, updating shipping address, switching to store pickup, extending pickup hold time, adding a pickup person, or rescheduling an appointment.
    - "late_lost": Use when the customer reports that an order is late, delayed, missing, or marked as delivered but not received.
    - "return_exchange": Use when the customer asks about returning or exchanging items, or inquires about general return policies and windows.
    - "price_match": Use when the customer asks about price matching a product against a competitor or Best Buy's price match guarantee.
    - "pickup_policy": Use when the customer asks specifically about the store pickup hold policy or what happens if they cannot pick up their order in time.

  Args:
      intent (str): The identified user intent.

  Returns:
      dict[str, Any]: Success status.
  """
  intent = intent.lower()
  valid_intents = [
      "check_status",
      "cancel",
      "modify",
      "late_lost",
      "return_exchange",
      "price_match",
      "pickup_policy",
  ]
  if intent not in valid_intents:
    return {
        "success": False,
        "error": f"Unknown intent: {intent}. Valid intents are check_status, cancel, modify, late_lost, return_exchange, price_match, pickup_policy.",
    }

  context.state["order_intent"] = intent
  if intent == "price_match":
    context.state["sms_link_event_id"] = "IVR_OS_PriceMatch"
  elif intent == "return_exchange":
    context.state["sms_link_event_id"] = "IVR_OS_ReturnExchange"
  else:
    context.state["sms_link_event_id"] = "IVR_OS_OrderStatus"

  tools.update_orders_instruction({"intent": intent})
  return {"success": True}
