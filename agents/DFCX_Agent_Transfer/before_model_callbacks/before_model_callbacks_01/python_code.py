import base64
import json
import pprint
import random

DFCX_AGENT = "projects/next-gen-ces-demos/locations/us/agents/b27d8077-ad1a-462a-8227-f7c678662d85"


def get_payload_part(payload_string: str):
  return Part(
      inline_data=ces_internal.Blob(
          data=base64.b64encode(payload_string.encode("utf-8")),
          mime_type="application/json",
      )
  )


def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
  params = callback_context.state.get("dfcx_params", {})
  # Merge fetch_init_json response into dfcx_params, cannot do it
  # inside the fetch_init_json function because we are calling
  # get_call_context and fetch_init_json in parallel and can't have
  # two functions updating the same variable at the same time.
  params.update(callback_context.state.get("init_json", {}))
  # Dialogflow agent requires throttle_level parameter set to a
  # float in the range [0, 1).
  params["throttle_level"] = random.random()

  # Dialogflow start page default parameters, needs to be set/sent
  # for proper functioning of dialogflow.
  params["inquiries_count"] = 0
  params["is_from_no_match"] = "false"
  params["nga_no_match_count"] = 0
  params["nga_no_input_count"] = 0
  params["is_from_no_input"] = "false"
  params["nga_repeat_count"] = 0
  params["nga_inquiries_count"] = 0
  params["nga_agent_request_count"] = 0
  params["needToFetchAppts"] = "true"
  params["nga_store_hours_intent_count"] = 0
  params["nga_vague_help_product_intent_count"] = 0
  params["PhoneNumber"] = params.get("phoneNumber") or params.get("PhoneNumber")
  params["phone_recapture"] = params.get("phoneNumber") or params.get(
      "PhoneNumber"
  )
  params["enable_fallback_and_reclassification"] = callback_context.state.get(
      "enable_fallback_and_reclassification", False
  )
  if "userQuery" not in params:
    print(f"TRANSFER_TO_CX: userQuery parameter is not set!")

  # Transfer payload
  payload = {
      "transferToDialogflow": DFCX_AGENT,
      "parameters": params,
      "userInput": params.get("userQuery", "Hi."),
  }
  print(f"TRANSFER_TO_CX: {pprint.pformat(payload)}")
  parts = [get_payload_part(json.dumps(payload))]

  return LlmResponse(content=Content(parts=parts), role="model")
