from typing import Any


def get_context_by_party_id() -> dict[str, Any]:
    """Retrieves service context for a given party ID, and determine if the proactive experience should be triggered or not from the response

    This must be called when entering the Check_Proactive subtask.
    The channel is automatically derived from the 'source' field in dfcx_params.

    Returns:
        dict: returns a dictionary with 2 parameters, paths parameter of type list, that would have the latest context created by the user, and a isProactive flag, that would indicate if the proactive experience is to be triggered or not.

        Success Schema (list of service paths):
          - paths (list[dict]): List of service path objects, each containing:
            - serviceContextNumber (str): Unique identifier for the service context.
            - link (str): URL to the adaptive support router.
            - ranking (int): Priority ranking of this service path.
            - type (str): The type of service path. Used to determine entitlement:
                - If any path has status.state = "AVAILABLE", user is entitled.
                - If no paths are available and any path type includes "PaidSupport",
                  offer_paid_support = True.
            - status (dict): Contains:
                - state (str): Current state of the path (e.g., "AVAILABLE").
                - updated (str): Timestamp of the last status update.
            - number (str): Unique path number identifier.
          - isProactive (bool): Flag indicating whether proactive support is enabled.

        Failure Schema:
            - agent_action (str): Explicit instructions that you, the AI agent, MUST
              follow immediately and exactly as written to recover from the failure.
    """
    session_id = context.state.get("call_id", context.session_id)
    channel_value = context.state["dfcx_params"].get("source", "")

    party_ids = context.state.get("party_ids", [])
    if not party_ids:
      return _handle_error("party_ids not set")
    party_id = party_ids[0]
    request_params = {
        "partyId": party_id,
        "channel": {
          "name" : channel_value
        }
    }

    parameters = {
        "x-session-id": session_id,
        "sessionInfo": {"parameters": {"request": request_params}},
    }

    try:
      mock = context.state.get("mock_get_service_context_by_partyid_response")
      if mock:
        response = mock
      else: 
        response = tools.get_context_by_party_id_getContextByPartyID(parameters).json()
        print(f"DEBUG: Raw response: {response}")

      if "sessionInfo" in response:
            data = response["sessionInfo"]["parameters"]["response"]
            return data
      else:
          return _handle_error(f"response for party_id {party_id}: {response}")
    except Exception as e:
      return _handle_error(
        f"ERROR: get_context_by_party_id failed - {e!r}"
      )


def _handle_error(error_message: str) -> dict[str, Any]:
  print(f"ERROR: get_context_by_party_id failed: {error_message}")
  # Return empty result on error, agent doesn't need to know
  # the tool call failed.
  return {}
    