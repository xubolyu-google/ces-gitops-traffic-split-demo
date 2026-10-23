from typing import Any

KEEP_FIELDS = ("display_name", "store_id")


def store_lookup() -> dict[str, Any]:
  """Performs a store lookup based on an entry point phone number.

  Returns:
    dict[str, Any]: A dictionary containing store details.
    Schema:
        - display_name (str): The display name of the store.
        - store_id (str): The store identifier.
  """
  if "customer_phone_number" not in context.state:
    return _handle_error("customer_phone_number not set")
  if "entry_point_phone_number" not in context.state:
    return _handle_error("entry_point_phone_number not set")

  parameters = {
      "sessionInfo": {
          "parameters": {
              "PhoneNumber": context.state["customer_phone_number"],
              "EntryPointNumber": context.state["entry_point_phone_number"],
          }
      },
  }
  try:
    mock = context.state.get("mock_store_lookup_response")
    if mock:
      response = mock
    else:
      response = tools.stores_storesLookup(parameters).json()
    if "sessionInfo" in response:
      data = response["sessionInfo"]["parameters"]
      context.state["dfcx_params"].update(data)

      # Dialogflow agent expects "storeID" instead of "store_id".
      context.state["dfcx_params"]["storeID"] = data.get("store_id")
      context.state["call_context"]["storeID"] = data.get("store_id")
      context.state["dfcx_params"]["storeID4"] = data.get("store_id4")
      context.state["call_context"]["storeID4"] = data.get("store_id4")
      if data.get("display_name", "N/A") == "N/A":
        data["display_name"] = None
      context.state["store_name"] = data["display_name"]
      if data.get("store_id", "N/A") == "N/A":
        data["store_id"] = None
      context.state["store_id"] = data["store_id"]

      return {k: data[k] for k in KEEP_FIELDS if k in data}
    else:
      return _handle_error(f"response: {response}")
  except Exception as e:
    return _handle_error(f"tool call or response parsing failed - {e!r}")


def _handle_error(error_message: str) -> dict[str, Any]:
  context.state["store_lookup_failure"] = error_message
  print(f"ERROR: store_lookup failed: {error_message}")
  # Return empty result on error, agent doesn't need to know
  # the tool call failed.
  return {}
