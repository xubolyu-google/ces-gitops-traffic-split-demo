from typing import Any
import uuid


def get_purchase_history(product_type: str) -> dict[str, Any]:
  """Retrieves the latest 3 years of purchase history for the customer to look for a match on the product_type the customer is experiencing issues with.

  Args:
      product_type (str, optional): The high level type of product. Must be one
        of the following exact strings:
        - "macbook": Use for Apple laptops.
        - "chromebook": Use for laptops running ChromeOS.
        - "computer": Use for all other laptops (Windows/Linux) or desktops
        - "iPad": Use for Apple tablets.
        - "tablet": Use for all non-Apple tablets (e.g., Samsung Galaxy Tab,
          Surface).
        - "printer": Inkjet, laser, or multifunction printers.
        - "scanner": Dedicated document scanners.
        - "fax": Dedicated fax machines.
        - "hard drive": External or internal storage devices (HDD/SSD).

  Returns:
      dict (str, list): A dictionary of purchases keyed by manufacturer.
        For each manufacturer, a list of dictionaries with a variety of info,
        including the product name and item id which the agent will need.
  """
  # Get list of party IDs, defaulting to a single-item list if only one exists, or empty list.
  party_ids = context.state.get("party_ids", [])
  if not party_ids:
    return _handle_error("party_ids not set")

  membership = context.state.get("membership", "")

  # Only lookup the first party_id (Best Buy Requirement, consistent with DFCX).
  party_id = party_ids[0]
  request_id = str(uuid.uuid4())
  parameters = {
      "product-name": product_type,
      "X-REQUEST_ID": request_id,
      "noOfYears": 3,
      "sessionInfo": {
          "parameters": {
              "request": {"partyId": party_id, "membership": membership}
          }
      },
  }
  try:
    mock = context.state.get("mock_purchase_history_response")
    if mock:
      response = mock
    else:
      response = tools.purchase_history_getPurchaseHistory(parameters).json()

    # Check for success structure
    if "sessionInfo" in response:
      purchases = response["sessionInfo"]["parameters"]["response"]["purchases"]

      aggregated_purchases = {}
      product_by_item_id = context.state["product_by_item_id"] = {}

      # Merge results into aggregated_purchases
      for brand, items in purchases.items():
        if brand not in aggregated_purchases:
          aggregated_purchases[brand] = []

        for item in items:
          item_id = item.get("itemId", str(uuid.uuid4()))
          product_by_item_id[item_id] = item

          aggregated_purchases[brand].append(
              {"product_name": item["productName"], "item_id": item_id, "productType": item["productType"], "sequenceNumber": item["sequenceNumber"], "skuId": item["skuId"], "orderNumber": item["orderNumber"],"purchaseDate": item["purchaseDate"],  "fourPartKey": item["fourPartKey"],"isCoveredByProtectionPlan": item["isCoveredByProtectionPlan"],
              "isUnderManufacturerWarranty": item["isUnderManufacturerWarranty"]}
          )
        return aggregated_purchases
    else:
      return _handle_error(f"response for party_id {party_id}: {response}")
  except Exception as e:
    return _handle_error(
        f"tool call or response parsing failed for party_id {party_id} - {e!r}"
    )


def _handle_error(error_message: str) -> dict[str, Any]:
  context.state["get_purchase_history_failure"] = error_message
  print(f"ERROR: get_purchase_history failed: {error_message}")
  # Return empty result on error, agent doesn't need to know
  # the tool call failed.
  return {}
