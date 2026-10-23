from typing import Any
 
 
def create_and_get_service_context() -> dict[str, Any]:
    """Creates and retrieves service context for a specific product selected by the customer from their purchase history.
 
    This must be called when entering the Determine_Service_Entitlement subtask.
    The channel is automatically derived from the 'source' field in dfcx_params.   
 
    Returns:
        dict[str, Any]: A list of service context paths ranked by priority.
 
        Success Schema (list of service paths):
            - serviceContextNumber (str): Unique identifier for the service context.
            - link (str): URL to the adaptive support router.
            - ranking (int): Priority ranking of this service path.
            - type (str): The type of service path. Used to determine entitlement:
              - If any path has status.state = "AVAILABLE", user is entitled.
              - If no paths are available and any path type includes "PaidSupport",
                offer_paid_support = True.
            - status (dict): Contains state and updated fields.
            - number (str): Unique path number identifier.
 
        Failure Schema:
            - agent_action (str): Explicit instructions that you, the AI agent, MUST
              follow immediately and exactly as written to recover from the failure.
    """
    party_ids = context.state.get("party_ids", [])
    if not party_ids:
      party_id = ""
    else:
      #Only lookup the first party_id (Best Buy Requirement, consistent with DFCX).
      party_id = party_ids[0]
    

    classification = context.state.get("computer_troubleshooting_issue_classification")
    if classification == "hardware":
      intentId= "troubleshooting.hardware"
    elif classification == "software":
      intentId = "troubleshooting.software"
    else:
      intentId = "troubleshooting.vague"
      
    session_id = context.state.get("call_id", context.session_id)
    channel_value = context.state["dfcx_params"].get("source", "")
    order_number = context.state.get("order_number", "")
    problem_description = context.state.get("user_problem", "")
    product_category = context.state.get("product_type", "")
    sku = context.state.get("sku_id", "")
    four_part_key = context.state.get("four_part_key", "")
    sequence_number = context.state.get("sequence_number", "")
    brand = context.state.get("brand", "")
    item_id = context.state.get("item_id", "")


    request_params = {
        "orderNumber": order_number,
        "problemDescription": problem_description,
        "channel": channel_value,
        "productCategory": product_category,
        "sku": sku,
        "itemId": item_id,
        "fourPartKey": four_part_key,
        "sequenceNumber": sequence_number,
        "partyId": party_id,
        "brand" : brand,
        "intentId" : intentId
    }
 
    parameters = {
        "x-session-id": session_id,
        "sessionInfo": {"parameters": {"request": request_params}},
    }
 
    try:
      mock = context.state.get("mock_create_and_get_service_context_response")
      if mock:
        response = mock
      else:
        response = tools.create_and_get_service_context_createAndGetServiceContext(parameters).json()

      # Check for success structure
      if "sessionInfo" in response:
        data = response["sessionInfo"]["parameters"]["response"]
        return data
      else:
        return _handle_error(f"response for party_id {party_id}: {response}")
    except Exception as e:
      return _handle_error(
        f"ERROR: Service context lookup failed - {e!r}"
      )


def _handle_error(error_message: str) -> dict[str, Any]:
  print(f"ERROR: create_and_get_service_context failed: {error_message}")
  # Return empty result on error, agent doesn't need to know
  # the tool call failed.
  return {}
    