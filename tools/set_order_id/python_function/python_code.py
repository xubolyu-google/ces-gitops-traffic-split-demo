from typing import Any


def set_order_id(order_id: str) -> dict[str, Any]:
  """Validates and sets the order_id in session state.

  Args:
      order_id (str): The ID of the order.

  Returns:
      dict[str, Any]: Success status.
  """
  orders_by_id = context.state.get("orders_by_id", {})

  if not orders_by_id:
    return {
        "success": False,
        "error": "No orders cached. Call get_orders_by_phone first.",
    }

  normalized_input = _normalize_id(order_id)

  matched_id = None
  for cached_id in orders_by_id.keys():
    if _normalize_id(cached_id) == normalized_input:
      matched_id = cached_id
      break

  if not matched_id:
    return {
        "success": False,
        "error": f"Order ID {order_id} is not valid for this customer.",
    }

  context.state["order_id"] = matched_id
  tools.update_orders_instruction({"identified_order": True})
  return {"success": True}


def _normalize_id(order_id: str) -> str:
  # Convert to uppercase, replace 'O' with '0', remove non-alphanumeric
  normalized = order_id.upper().replace("O", "0")
  return "".join(c for c in normalized if c.isalnum())
