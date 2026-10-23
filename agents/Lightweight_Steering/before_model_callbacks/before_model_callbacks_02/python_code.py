from typing import Any

DISCLAIMER = (
    "You're interacting with a virtual assistant that'll use AI to help you."
    " I'm still learning, so I may not get everything right. For quality"
    " assurance, your call may be recorded. By continuing, you accept the terms"
    " of use and privacy policy on BestBuy.com."
)
EXTENSION = "If you have an extension, please say extension."
SPANISH = "Para español, diga español."
SOLICITATION = "Now, what can I help you with?"


def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
  greeting_stage = callback_context.state.get("greeting_stage", "NOT_STARTED")
  if greeting_stage == "DONE":
    # Hide the following tools so that LLM will not use them again.
    llm_request.config.hide_tool("get_call_context")
    llm_request.config.hide_tool("fetch_init_json")
    llm_request.config.hide_tool("store_lookup")
    llm_request.config.hide_tool("ani_lookup")
    return None

  # Disable barge-in immediately before disclaimer or tool calls. Without this,
  # if a user were to make noise between the tool calls and initial disclaimer,
  # they would successfully barge-in. This is exacerbated if tool calls are
  # slower.
  if greeting_stage == "NOT_STARTED":
    callback_context.state["greeting_stage"] = "DISABLED_BARGE_IN"
    start_disable_barge_in = LlmResponse.from_parts(
        [Part.from_customized_response(content="", disable_barge_in=True)]
    )
    start_disable_barge_in.partial = True
    return start_disable_barge_in

  # Call get_call_context on session start.
  if greeting_stage == "DISABLED_BARGE_IN":
    callback_context.state["greeting_stage"] = "DISCLAIMER"
    return LlmResponse.from_parts(
        parts=[
            Part.from_function_call(name="get_call_context", args={}),
            Part.from_function_call(name="fetch_init_json", args={}),
        ]
    )

  # Call store_lookup immediately after the get_call_context call.
  if any(
      part.has_function_response("get_call_context")
      for part in llm_request.contents[-1].parts
  ):
    return LlmResponse.from_parts(
        parts=[Part.from_function_call(name="store_lookup", args={})]
    )

  # Play no barge-in greeting and ani_lookup immediately after the
  # store_lookup call.
  if any(
      part.has_function_response("store_lookup")
      for part in llm_request.contents[-1].parts
  ):
    store_name = callback_context.state.get("store_name")
    if store_name:
      greeting = f"Welcome to Best Buy {store_name}. {DISCLAIMER}"
    else:
      greeting = f"Welcome to Best Buy. {DISCLAIMER}"
    no_barge_in_greeting = Part.from_customized_response(
        content=greeting, disable_barge_in=True
    )
    ani_lookup = Part.from_function_call(name="ani_lookup", args={})
    callback_context.state["greeting_stage"] = "PROACTIVE"
    return LlmResponse.from_parts(parts=[no_barge_in_greeting, ani_lookup])

  # After ani_lookup, play membership acknowledgement, spanish/extension
  # message, emergency message, and proactive message or solicit call reason.
  if any(
      part.has_function_response("ani_lookup")
      for part in llm_request.contents[-1].parts
  ):
    membership = callback_context.state.get("membership")
    messages = []
    if membership in ("Total", "Plus"):
      messages.append(
          f"And thanks for being a My Best Buy {membership} member."
      )

    if callback_context.state.get("store_name"):
      messages.append(EXTENSION)
      emergency_message = callback_context.state.get("emergency_message_retail")
      if emergency_message:
        messages.append(emergency_message)
    else:
      messages.append(SPANISH)
      emergency_message = callback_context.state.get(
          "emergency_message_national"
      )
      if emergency_message:
        messages.append(emergency_message)

    messages.extend(get_proactive_message(callback_context.state))

    parts = []
    # Play all except the last message.
    if len(messages) > 1:
      parts.append(
          Part.from_customized_response(
              content=" ".join(messages[:-1]), disable_barge_in=False
          )
      )
    # Play the last message which is a question. The no input handling will replay
    # the last message.
    parts.append(
        Part.from_customized_response(
            content=messages[-1], disable_barge_in=False
        )
    )

    callback_context.state["greeting_stage"] = "DONE"
    return LlmResponse.from_parts(parts=parts)

  return None


def get_proactive_message(state: dict[str, Any]) -> list[str]:
  proactive_code = state.get("proactive_code")
  messages = []
  examples_list = []
  example_proactive_message = ""

  if proactive_code == "APT":
    appointment_type = state.get("appointment_type")
    if appointment_type == "Repair":
      proactive_message = (
          "I see you have an upcoming in-home service appointment. Is that why"
          " you're calling?"
      )
      example_proactive_message = proactive_message
      messages = [proactive_message]
      examples_list.append(
          f"""  <example name="Happy Path: Proactive Repair Appointment">
    - Agent: "{example_proactive_message}"
    - User: Yes.
    - [TOOL_CALL: connect_to_dfcx_agent(user_query:"I am calling about my upcoming in-home service appointment.", is_proactive_routing:True)]
  </example>"""
      )
    elif appointment_type == "InstallDelivery":
      proactive_message = (
          "I see you have an upcoming home delivery or installation"
          " appointment. Is that why you're calling?"
      )
      example_proactive_message = proactive_message
      messages = [proactive_message]
      examples_list.append(
          f"""  <example name="Happy Path: Proactive Install/Delivery Appointment">
    - Agent: "{example_proactive_message}"
    - User: Yes.
    - [TOOL_CALL: connect_to_dfcx_agent(user_query:"I am calling about my upcoming home delivery or installation appointment.", is_proactive_routing:True)]
  </example>"""
      )

  elif proactive_code == "PICKUP":
    store_pickup_count = int(state.get("store_pickup_count", 0))
    if store_pickup_count == 1:
      proactive_message = (
          "Just to let you know, you have an order with 1 item ready to pick up"
          " in store."
      )
    else:
      proactive_message = (
          f"Just to let you know, you have an order with {store_pickup_count}"
          " items ready to pick up in store."
      )
    messages = [proactive_message, SOLICITATION]
    example_proactive_message = (
        "Just to let you know, you have an order with 3 items ready to pick up"
        f" in store. {SOLICITATION}"
    )
    examples_list.append(
        f"""  <example name="Proactive Pickup Notification, Check Status">
    - Agent: "{example_proactive_message}"
    - User: "I want to check my order status".
    - [TOOL_CALL: route_order_management_intent(user_query:"I want to check my order status.")]
  </example>"""
    )

  elif proactive_code == "ORDERS":
    open_orders_count = int(state.get("open_orders_count", 0))
    if open_orders_count > 1:
      proactive_message = (
          f"I see you have {open_orders_count} open orders with us. Are you"
          " calling about one of those orders?"
      )
      messages = [proactive_message]
      example_proactive_message = (
          "I see you have 3 open orders with us. Are you calling about one of"
          " those orders?"
      )
      examples_list.append(
          f"""  <example name="Happy Path: Proactive Multiple Orders">
    - Agent: "{example_proactive_message}"
    - User: Yes.
    - [TOOL_CALL: route_order_management_intent(user_query:"I am calling about one of my open orders.")]
  </example>"""
      )
    elif open_orders_count == 1:
      status = state.get("single_order_status", "unknown")
      proactive_message = (
          f"I see you have an order whose status is, {status}. Is that why"
          " you're calling?"
      )
      messages = [proactive_message]
      example_proactive_message = (
          "I see you have an order whose status is, delayed. Is that why you're"
          " calling?"
      )
      examples_list.append(
          f"""  <example name="Happy Path: Proactive Order Check">
    - Agent: "{example_proactive_message}"
    - User: Yes, it is.
    - [TOOL_CALL: route_order_management_intent(user_query:"I am calling about the order whose status is delayed.")]
  </example>"""
      )

  elif proactive_code == "REPAIR_COMPLETE":
    proactive_message = (
        "It looks like your repair is complete, and pickup needs to be"
        " scheduled online. Can I send you a text with a link to that page?"
    )
    messages = [proactive_message]
    example_proactive_message = proactive_message
    examples_list.append(
        f"""  <example name="Proactive In-Store Repair Complete, User Confirms">
    - Agent: "{example_proactive_message}"
    - User: Yes.
    - [TOOL_CALL: transfer_to_offer_text_agent()]
  </example>"""
    )

  elif proactive_code == "REPAIR_IN_PROGRESS":
    proactive_message = (
        "It looks like your device is being repaired. Is that why you're"
        " calling today?"
    )
    messages = [proactive_message]
    example_proactive_message = proactive_message
    examples_list.append(
        f"""  <example name="Proactive In-Store Repair In Progress, User Confirms">
    - Agent: "{example_proactive_message}"
    - User: Yes.
    - Agent: "Got it. Would you like to check the status of that repair?"
    - User: Yes.
    - [TOOL_CALL: connect_to_dfcx_agent(user_query:"check repair status", is_proactive_routing:True)]
  </example>
  <example name="Proactive In-Store Repair In Progress, Ambiguous Repair-Related Response">
    - Agent: "{example_proactive_message}"
    - User: "When will it be done?"
    - Agent: "Got it. Would you like to check the status of that repair?"
    - User: "Yes."
    - [TOOL_CALL: connect_to_dfcx_agent(user_query:"check repair status", is_proactive_routing:True)]
  </example>"""
    )

  elif proactive_code == "AUTH":
    proactive_message = (
        "We see there's a payment issue with your My Best Buy membership. To"
        " avoid losing benefits, you need to update your credit card on your"
        " membership page online. Do you want to take care of that now?"
    )
    messages = [proactive_message]
    example_proactive_message = proactive_message
    examples_list.append(
        f"""  <example name="Proactive Membership Payment Check">
    - Agent: "{example_proactive_message}"
    - User: Yes.
    - [TOOL_CALL: connect_to_dfcx_agent(user_query:"I want to update credit card for my membership.", is_proactive_routing:True)]
  </example>"""
    )

  else:
    messages = [SOLICITATION]

  # If we have a proactive example, also append the "User Ignores Proactive" example
  if examples_list:
    ignore_example = f"""  <example name="User Ignores Proactive">
    - Agent: "{example_proactive_message}"
    - User: "No I have a question about iPhones".
    - Agent: "Got it, what's your question about iPhones?"
    - User: I want to know if you have the iPhone 17 in stock.
    - [TOOL_CALL: connect_to_dfcx_agent(user_query:"I want to know if you have the iPhone 17 in stock.")]
  </example>
  <example name="User Ignores Proactive, Clarification Needed">
    - Agent: "{example_proactive_message}"
    - User: "I'm calling about my membership."
    - Agent: "Got it. Could you clarify what you need help with regarding your membership?"
    - User: "I want to cancel it."
    - [TOOL_CALL: connect_to_dfcx_agent(user_query:"I want to cancel my membership.")]
  </example>
  <example name="User Ignores Proactive, Requests Live Agent">
    - Agent: "{example_proactive_message}"
    - User: "Can I just talk to someone at the store?"
    - [TOOL_CALL: connect_to_live_agent_request_menu()]
  </example>"""
    examples_list.append(ignore_example)
    state["steering_proactive_examples"] = "\n".join(examples_list)
  else:
    state["steering_proactive_examples"] = ""

  return messages
