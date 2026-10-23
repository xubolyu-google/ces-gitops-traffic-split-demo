from typing import Any


def get_orders_by_phone() -> dict[str, Any]:
  """Retrieves order information for all orders associated with the customer's phone number.

  Returns:
      dict[str, Any]: A dictionary containing high-level order summaries.
  """
  order_phone_number = context.state.get("order_phone_number")
  customer_phone_number = context.state.get("customer_phone_number")
  phone_number = order_phone_number or customer_phone_number

  if not phone_number:
    return _handle_error(
        "Neither order_phone_number nor customer_phone_number set in context"
    )

  order_details_raw = None
  if (
      (not order_phone_number or order_phone_number == customer_phone_number)
      and customer_phone_number
      and context.state.get("cached_ani_orders")
  ):
    order_details_raw = context.state.get("cached_ani_orders")
  else:
    combined_params = {
        "sessionInfo": {
            "parameters": {"orderRequest": {"orderPhoneNumber": phone_number}}
        }
    }

    try:
      mock = context.state.get("mock_get_orders_by_phone_response")
      if mock:
        if "sessionInfo" not in mock and phone_number in mock:
          response = mock[phone_number]
        else:
          response = mock
      else:
        response = tools.order_getOrderByPhone(combined_params).json()

      # Check for success structure
      if "sessionInfo" in response:
        order_details_raw = (
            response.get("sessionInfo", {})
            .get("parameters", {})
            .get("orderDetails")
        )
      else:
        return _handle_error(f"Invalid response structure: {response}")
    except Exception as e:
      return _handle_error(f"tool call or response parsing failed - {e!r}")

  if not order_details_raw:
    return {}

  if isinstance(order_details_raw, dict):
    orders_list = order_details_raw.get("orderDetails", [])
  elif isinstance(order_details_raw, list):
    orders_list = order_details_raw
  else:
    orders_list = []
  # Caching full details
  orders_by_id = context.state["orders_by_id"] = {}
  summaries = []

  for order in orders_list:
    order_id = order.get("id")
    if order_id:
      orders_by_id[order_id] = order

    # Sort items by price descending, ignoring free gifts.
    items = order.get("orderItems", [])
    non_free_gifts = [item for item in items if not item.get("isFreeGift")]

    sorted_items = sorted(non_free_gifts, key=_get_price, reverse=True)
    items_summary = [item.get("itemDescription") for item in sorted_items]
    summaries.append({
        "order_id": order_id,
        "created_date": order.get("createdCalendarDate"),
        "total": order.get("total"),
        "items": items_summary,
    })

  # Persist orders_by_id dictionary back to state
  context.state["orders_by_id"] = orders_by_id
  context.state.pop("order_id", None)
  tools.update_orders_instruction({
      "fetched_orders": bool(orders_by_id),
      "identified_order": False,
  })

  return {"orderDetails": summaries}


def _get_price(item: dict[str, Any]) -> float:
  price = item.get("price")
  if isinstance(price, dict):
    total = price.get("itemTotal")
    try:
      return float(total) if total is not None else 0.0
    except (ValueError, TypeError):
      return 0.0
  return 0.0


def _handle_error(error_message: str) -> dict[str, Any]:
  context.state["get_orders_by_phone_failure"] = error_message
  print(f"ERROR: get_orders_by_phone failed: {error_message}")
  return {}
