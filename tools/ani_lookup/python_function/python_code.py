from typing import Any

KEEP_FIELDS = (
    "zipCode",
    "firstName",
    "lastName",
    "email",
)

FIELDS_TO_STORE_IN_CALL_CONTEXT = (
    "zipCode",
    "memberID",
    "membershipStatus",
    "partyID",
    "groupStatus",
    "fulfillmentType",
    "appointmentDate",
    "getItByDate",
)

# Default values when the field has no value.
DEFAULTS = ("1990-01-01T00:00:00-05:00", "none")


def ani_lookup() -> dict[str, Any]:
  """Performs an ANI (Automatic Number Identification) lookup using the customer phone number to retrieve customer and order-related metadata.

  Returns:
    dict[str, Any]: A dictionary containing ANI details.
    Schema:
        - zipCode (str): Customer's zip code.
        - firstName (str): Customer's first name.
        - lastName (str): Customer's last name.
        - email (str): Customer's email address.
  """
  if "customer_phone_number" not in context.state:
    return _handle_error("customer_phone_number not set")

  # Do not perform ANI lookup if the phone number is in the denylist.
  denylist_lookup_result = tools.ani_denylist_lookup({}).json()["result"]
  if "isANIDenyListed" in denylist_lookup_result:
    if denylist_lookup_result["isANIDenyListed"]:
      return _handle_error("customer phone number is in the denylist")
  else:
    return _handle_error("skipping due to ani denylist lookup failure")

  session_id = context.state.get("call_id", context.session_id)
  parameters = {
      "x-session-id": session_id,
      "includeOrders": True,
      "sessionInfo": {
          "parameters": {"phoneNumber": context.state["customer_phone_number"]}
      },
  }
  try:
    mock = context.state.get("mock_ani_lookup_response")
    if mock:
      response = mock
    else:
      response = tools.ANI_aniLookup(parameters).json()
    if "sessionInfo" in response:
      data = response["sessionInfo"]["parameters"]
      context.state["dfcx_params"].update(data)

      if not data.get("with_ani_lookup"):
        return _handle_error("customer phone number not found")

      for field in FIELDS_TO_STORE_IN_CALL_CONTEXT:
        if field in data:
          context.state["call_context"][field] = data[field]

      # Clear any field that has the default value.
      def clear_default_values(d):
        for k, v in d.items():
          if isinstance(v, dict):
            clear_default_values(v)
          elif isinstance(v, str) and v in DEFAULTS:
            d[k] = None

      clear_default_values(data)

      proactive = data.get("isProactive", {})
      orders = data.get("orders", {})
      context.state["cached_ani_orders"] = orders
      order_details = orders.get("orderDetails", [])

      if proactive.get("isRepairAppointment"):
        context.state["proactive_code"] = "APT"
        context.state["appointment_type"] = "Repair"
      elif proactive.get("isOrderInstallDelivery"):
        context.state["proactive_code"] = "APT"
        context.state["appointment_type"] = "InstallDelivery"
      elif proactive.get("isOpenRepairInProgress"):
        context.state["proactive_code"] = "REPAIR_IN_PROGRESS"
      elif proactive.get("isOpenRepairComplete"):
        context.state["proactive_code"] = "REPAIR_COMPLETE"
      elif proactive.get("isOrderReadyForPickUp") and orders.get(
          "storePickupCountLatest"
      ):
        context.state["proactive_code"] = "PICKUP"
        context.state["store_pickup_count"] = orders.get(
            "storePickupCountLatest"
        )
      elif data.get("open_orders_count_15d", 0) == 1 and len(order_details) > 0:
        if (
            order_details[0].get("itemStats", {}).get("distinctStatusCount", 0)
            == 1
        ):
          context.state["proactive_code"] = "ORDERS"
          context.state["open_orders_count"] = data["open_orders_count_15d"]
          order_items = order_details[0].get("orderItems", [])
          if len(order_items) > 0:
            context.state["single_order_status"] = (
                order_items[0]
                .get("customerStatusInfo", {})
                .get("shortDescription")
            )
      elif data.get("open_orders_count_15d", 0) > 1:
        context.state["proactive_code"] = "ORDERS"
        context.state["open_orders_count"] = data["open_orders_count_15d"]
      elif proactive.get("isFailedAuthMembership"):
        context.state["proactive_code"] = "AUTH"

      if "firstName" in data:
        context.state["first_name"] = data["firstName"]
      if "lastName" in data:
        context.state["last_name"] = data["lastName"]
      if "email" in data:
        context.state["email"] = data["email"]
      if "membership" in data:
        context.state["membership"] = data["membership"]
      if (
          "partyID" in data
          and isinstance(data["partyID"], list)
          and len(data["partyID"]) > 0
      ):
        context.state["party_ids"] = data["partyID"]
        context.state["call_context"]["partyID"] = data["partyID"][0]

      return {k: data[k] for k in KEEP_FIELDS if k in data}
    else:
      return _handle_error(f"response: {response}")
  except Exception as e:
    return _handle_error(f"tool call or response parsing failed - {e!r}")


def _handle_error(error_message: str) -> dict[str, Any]:
  context.state["ani_lookup_failure"] = error_message
  print(f"ERROR: ani_lookup failed: {error_message}")
  # Return empty result on error, agent doesn't need to know
  # the tool call failed.
  return {}
