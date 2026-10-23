from datetime import datetime
from typing import Any


def get_order_details(
    for_cancellation: bool = False,
    for_modification: bool = False,
) -> dict[str, Any]:
  """Retrieves filtered details for the active order from the cached orders.

  Args:
      for_cancellation (bool): If True, include cancellation related fields.
      for_modification (bool): If True, include modification related fields.

  Returns:
      dict[str, Any]: A dictionary containing the filtered order details.
  """
  order_id = context.state.get("order_id")
  if not order_id:
    return _handle_error(
        "No order_id set in session state. Call set_order_id first."
    )

  orders_by_id = context.state.get("orders_by_id", {})

  if not orders_by_id:
    return _handle_error("No orders cached in session state.")

  order = orders_by_id.get(order_id)

  if not order:
    return _handle_error(f"Order with ID {order_id} not found in cache.")

  # Progressive Disclosure
  filtered_order = {
      "id": order.get("id"),
      "createdCalendarDate": order.get("createdCalendarDate"),
      "is3POrder": order.get("is3POrder"),
      "3POrderEligibleForEscalation": order.get("3POrderEligibleForEscalation"),
      "paymentStatus": order.get("paymentStatus"),
  }

  order_items = order.get("orderItems", [])
  filtered_items = []

  appointment_ids = {
      item.get("installDeliveryAppointmentId")
      for item in order_items
      if order.get("isDeliveryInstallOrder")
      and order.get("isOutForDelivery")
      and item.get("installDeliveryAppointmentId")
  }

  arrival_times = {}
  if appointment_ids:
    try:
      arrival_times = tools.get_home_appointment_arrival_time({
          "appointment_ids": list(appointment_ids)
      }).json().get("result", {})
    except Exception as e:
      print(f"ERROR: get_home_appointment_arrival_time failed: {e!r}")

  for item in order_items:
    # Ignore free gifts.
    if item.get("isFreeGift"):
      continue
    # Ignore DeliveryService since the product status should already cover delivery.
    if item.get("type") == "DeliveryService":
      continue
    status_info = item.get("customerStatusInfo", {})
    item_status = (
        status_info.get("voiceDescription")
        or status_info.get("shortDescription")
        or item.get("status", {}).get("description")
    )
    is_curbside = any(
        n.get("id") == "curbsidePickupInstructions"
        for n in item.get("navigations", [])
    )
    if is_curbside:
      item_status += (
          " When you arrive, please park in a designated curbside pickup space"
          " and check in to let us know you're here."
      )
    context.state.pop("sms_fields", None)
    if (
        (appt_id := item.get("installDeliveryAppointmentId"))
        and appt_id in arrival_times
    ):
      context.state["sms_link_event_id"] = "IVR_HA_DeliveryTracker"
      context.state["sms_fields"] = {
        "orderId": order.get("id"),
        "startDateTime": item.get("appointment", {}).get("start")
      }
      arrival_info = arrival_times[appt_id]
      if (eta := arrival_info.get("customerCommunicatedETA")) and eta.get("time"):
        item_status = f"Out for delivery: the estimated time of arrival is today around {eta['time']}. {item_status}"
      elif (start := arrival_info.get("arrivalWindowStartTime")) and (
          finish := arrival_info.get("arrivalWindowFinishTime")
      ):
        if start.get("time") and finish.get("time"):
          item_status = f"Out for delivery: the arrival window is today between {start['time']} to {finish['time']}. {item_status}"

    filtered_item = {
        "description": item.get("itemDescription"),
        "status": item_status,
    }
    if is_curbside:
      filtered_item["curbside_eligible"] = True
    if (price := item.get("price", {}).get("itemTotal")) is not None:
      filtered_item["price"] = price
    if (
        (appointment := item.get("appointment"))
        and appointment.get("start")
        and appointment.get("end")
    ):
      filtered_item["appointment"] = {
          "start": appointment.get("start"),
          "end": appointment.get("end"),
      }
    if "trackingInfo" in item:
      kept_fields = (
          "carrier",
          "expectedArrivalDate",
          "shipmentDate",
          "expectedShipDate",
          "trackingNumber",
          "deliveryPhotoUri",
      )
      tracking_info = {
          k: v.removesuffix("T00:00:00")
          for k, v in item["trackingInfo"].items()
          if k in kept_fields
      }
      if "deliveryPhotoUri" in item["trackingInfo"]:
        tracking_info["deliveryPhotoAvailable"] = True
      if tracking_info:
        filtered_item["trackingInfo"] = tracking_info

    if for_cancellation:
      # Include cancellation flags for item if any
      mod_flags = item.get("status", {}).get("itemModificationFlag", {})
      if "isCancellable" in mod_flags:
        filtered_item["isCancellable"] = mod_flags["isCancellable"]

    if for_modification:
      # Include modification flags for item
      mod_flags = item.get("status", {}).get("itemModificationFlag", {})
      filtered_item["itemModificationFlag"] = mod_flags

    filtered_items.append(filtered_item)

  filtered_order["orderItems"] = filtered_items

  if for_cancellation or for_modification:
    # Include itemStats which contains roll-up counts
    filtered_order["itemStats"] = order.get("itemStats", {})

  return filtered_order


def _handle_error(error_message: str) -> dict[str, Any]:
  context.state["get_order_details_failure"] = error_message
  print(f"ERROR: get_order_details failed: {error_message}")
  return {}
