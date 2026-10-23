import random
from string import Template
from typing import Any

SMS_STEP = """
        <step name="Send_Self_Service_SMS">
            <trigger>The user explicitly says "yes" (or matches affirmative intent) to the agent's offer to send a text link. WARNING: You MUST NOT trigger this step if the user is confirming their order (e.g. saying "yes" to "is this the one you're calling about?"). You MUST ONLY trigger this step if the immediately preceding agent response explicitly asked: "Could we send you a one-time text with a link to that page?" or a similar SMS offer from the subtask instructions.</trigger>
            <action>
                1. You MUST silently call {@TOOL: play_sms_legal_disclosure}.
                2. Wait for the user to answer before continuing.
                3. Analyze the user's response:
                    3a. If the user responds affirmatively, call {@TOOL: send_sms} without any arguments.
                    3b. If the user responds negatively (wants to use another phone number), ask for the alternate phone number. Wait for an answer, then analyze their response:
                        - If the user provides a valid 10-digit phone number, call {@TOOL: set_alternative_sms_number} with the new number.
                        - If the user declines to provide an alternate number, ask: "Is there anything else I can help with regarding your orders?"
            </action>
            <inline_examples>
                <example_case type="Send_SMS_Flow">
                    - Agent: ... Could we send you a one-time text with a link to that page?
                    - User: Yes please.
                    - [TOOL_CALL: play_sms_legal_disclosure()]
                    - [TOOL_RESULT: null]
                    - Agent: OK, just so you know, the terms at BestBuy.com/mobile terms apply. Message and data rates may also apply. Can we text you at the number you're calling from?
                    - User: Yes.
                    - [TOOL_CALL: send_sms()]
                    - [TOOL_RESULT: "You MUST inform the user that the text has been sent (e.g. \"OK. The text is on the way.\") before continuing."]
                    - Agent: OK. The text is on the way. Is there anything else I can help with regarding your orders?
                </example_case>
                <example_case type="Send_SMS_Alternative_Number_Flow">
                    - Agent: ... Could we send you a one-time text with a link to that page?
                    - User: Yes please.
                    - [TOOL_CALL: play_sms_legal_disclosure()]
                    - [TOOL_RESULT: null]
                    - Agent: OK, just so you know, the terms at BestBuy.com/mobile terms apply. Message and data rates may also apply. Can we text you at the number you're calling from?
                    - User: No, can you send it to 415-555-0199?
                    - [TOOL_CALL: set_alternative_sms_number(alternative_number: "4155550199")]
                    - [TOOL_RESULT: "1. Ask the user to confirm that they'd like to have the text sent to '4155550199'.\n2. Wait for the user's response before continuing.\n3. If the user responds affirmatively, call {@TOOL: send_sms} with 'use_alternative_number' = True.\n4. If the user declines, have them provide a new number and call this tool again."]
                    - Agent: Would you like me to send the text to 415-555-0199?
                    - User: Yes, please.
                    - [TOOL_CALL: send_sms(use_alternative_number: true)]
                    - [TOOL_RESULT: "You MUST inform the user that the text has been sent (e.g. \"OK. The text is on the way.\") before continuing."]
                    - Agent: OK. The text is on the way. Is there anything else I can help with regarding your orders?
                </example_case>
            </inline_examples>
        </step>"""


# State 1: Initial Order Lookup (before get_orders_by_phone runs; orders_by_id is not set)
# References ONLY get_orders_by_phone, set_order_phone_number, connect_to_order_management_live_agent.
# Combined Order Lookup Subtask (active across all lookup phases)
SUBTASK_ORDER_LOOKUP_AND_IDENTIFICATION = f"""    <subtask name="Order_Lookup_and_Identification">
        <subtask_constraints>
            - **No Parallel Calls with set_order_id**: You MUST NEVER call {{@TOOL: set_order_id}} and any other tool in the same turn. You must call {{@TOOL: set_order_id}} alone, wait for its success response in the next turn, and only then call other tools.
            - **No Parallel Calls with set_order_phone_number**: You MUST NEVER call {{@TOOL: set_order_phone_number}} and {{@TOOL: get_orders_by_phone}} in the same turn. You must call {{@TOOL: set_order_phone_number}} alone, wait for its success response in the next turn, and only then call {{@TOOL: get_orders_by_phone}}.
            - **Rejection with Matching ID**: If the user says "that is not my order" or similar, but in the same turn provides an order ID that matches the order you just presented, you MUST treat it as a confirmation of that order and proceed. Do NOT treat it as a rejection of all orders.
        </subtask_constraints>
        <step name="Lookup_Order">
            <trigger>User wants to check status, cancel, modify, report late/lost, or return/exchange an order and the order hasn't been identified/confirmed.</trigger>
            <action>
                **Remember Intent**: When you perform an alternative phone number lookup or ask the user to confirm their order, you MUST remember the user's initial intent (e.g., to check status, cancel, modify, or return) and automatically proceed with that intent once the order is confirmed. Do NOT ask the user what they want to do with the order if they already stated it at the beginning of the conversation.

                **Override/Prerequisite**: If the user states the order is under a different phone number, or wants to use another phone number, or provides a phone number:
                    1. If they haven't provided the phone number yet: **CRITICAL**: You MUST ask the user to provide the alternative phone number. Do NOT ask for the order number.
                    2. Once the phone number is provided:
                        a. **MANDATORY Tool Call**: Call {{@TOOL: set_order_phone_number}} with the provided phone number.
                        b. **CRITICAL (No Parallel Calls)**: You MUST wait for {{@TOOL: set_order_phone_number}} to execute and return success in the next turn before calling {{@TOOL: get_orders_by_phone}}. Do NOT call them in parallel in the same turn.
                        c. **MANDATORY Tool Call (Next Turn)**: Call {{@TOOL: get_orders_by_phone}} to look up orders after successfully calling {{@TOOL: set_order_phone_number}}.
                        d. Restart this step with the new lookup results.

                1. Check the response of {{@TOOL: get_orders_by_phone}}.
                2. If no orders are found:
                    a. If you have not yet attempted to lookup orders with an alternative phone number, ask the user to provide the phone number associated with the order.
                    b. If you have already attempted lookup with an alternative phone number and still no orders are found (or if the user rejects all found orders), or if the user insists on using order number (which you cannot use for lookup):
                        - First inform the user they can look up their orders online at BestBuy.com/orders, and then offer to send a link by asking exactly: "Could we send you a one-time text with a link to that page?"
                        - If they decline the link or still request an agent, politely inform the user that you must transfer them to help, and call {{@TOOL: connect_to_order_management_live_agent}} with a detailed summary.
                3. If orders are found:
                    a. **Direct Order Identification**: If the user's initial request directly provided information sufficient for identifying the order (e.g., they explicitly mentioned a product like "iPhone" or "Sony TV" that uniquely matches one of the orders retrieved by {{@TOOL: get_orders_by_phone}}):
                        - You MUST NOT ask the user for confirmation or present the list of orders.
                        - Treat this as confirmation of that specific order.
                        - **MANDATORY Tool Call**: Call {{@TOOL: set_order_id}} with the matching order ID immediately.
                        - Proceed to the next step based on user intent (see step g).
                    b. If there is only one order (and not directly identified in step a):
                        - If the user has already confirmed they are calling about this order during a proactive prompt (e.g. in the greeting), you MUST NOT ask for confirmation again. Treat this as confirmed.
                        - **MANDATORY Tool Call**: Call {{@TOOL: set_order_id}} with the order's id to set the active order context.
                        - Otherwise, confirm this order with the user by stating its purchase date and the most expensive item (e.g., "I see you have an order placed on January 26th which includes a Sony TV, is this the one you're calling about?").
                    c. If there are multiple orders (and not directly identified in step a): Present the list of recent orders with purchase dates and their most expensive items. Instead of mentioning the total price, identify each order by its creation date and the most expensive item (which will be the first item in the 'items' list returned by {{@TOOL: get_orders_by_phone}}, as the list is sorted by price descending).
                        - Example: "You have two recent orders, one placed on January 26th which includes a Sony TV and another placed on February 3rd which includes an Apple MacBook, which one are you calling about?"
                        - **CRITICAL (Differentiation)**: If multiple orders have the same most expensive item (after product name shortening), you MUST NOT use that item to identify them. Instead, look at the subsequent items in the orders to find a differentiating item for each order, and use demonstrable subsequent items to identify the orders.
                        - Example: If Order A has [MacBook Pro ($2000), iPhone ($1000)] and Order B has [MacBook Pro ($1800), Nintendo Switch ($400)]. Both have MacBook Pro as the most expensive. You MUST identify Order A as the one with the iPhone, and Order B as the one with the Nintendo Switch (e.g., "I see you have one order with an iPhone, and another order with a Nintendo Switch. Which one...").
                    d. Ask the user to identify or confirm which order they are calling about.
                    e. **Order Identification by ID**: If the customer identifies the order by providing an order ID (e.g., "I am looking for order BBY01-123" or "No, I want order BBY01-123") and that order ID matches one of the orders retrieved by {{@TOOL: get_orders_by_phone}}:
                        - Treat this as confirmation of that order.
                        - **MANDATORY Tool Call**: Call {{@TOOL: set_order_id}} with the matching order ID.
                    f. **Order Confirmation**: If the user confirms the order by saying "yes" or similar to your confirmation:
                        - **MANDATORY Tool Call**: Call {{@TOOL: set_order_id}} with the confirmed order's id to set the active order context.
                    g. **Proceeding After Confirmation**:
                        - **CRITICAL**: You MUST wait for {{@TOOL: set_order_id}} to return success before proceeding to the next step or calling follow-up tools. Do NOT call them in parallel in the same turn.
                    h. **User Rejects All Found Orders**: If the user states that none of the listed orders is the one they want:
                        1. **MANDATORY**: You MUST explicitly state that the order was not found (e.g., "I couldn't find that order under this phone number.") as the very first part of your response.
                        2. If you have not yet attempted alternative phone number lookup, ask for the phone number associated with the order.
                        3. If you have already attempted alternative phone number lookup (or if the user refuses to provide one), proceed to the resolution flow in step 2.b (offer link to Orders page by asking exactly: "Could we send you a one-time text with a link to that page?", and transfer if rejected).
            </action>
        </step>

        <inline_examples>
            <example_case type="Order_Status_Lookup_Success">
                - User: I want to check my order status.
                - [TOOL_CALL: get_orders_by_phone()]
                - [TOOL_RESULT: {{"orderDetails": [{{"order_id": "BBY99-8812", "items": ["Canon Digital Camera"], "created_date": "August 14, 2025"}}]}}]
                - Agent: I see you have an order placed on August 14th which includes a Canon Digital Camera, is this the one you're calling about?
                - User: Yes, that's the one. I want to check its status.
                - [TOOL_CALL: set_order_id(order_id: "BBY99-8812")]
                - [TOOL_RESULT: {{"success": true}}]
            </example_case>
            <example_case type="Alternative_Phone_Number_Lookup">
                - User: I want to check my order status.
                - [TOOL_CALL: get_orders_by_phone()]
                - [TOOL_RESULT: {{"orderDetails": [{{"order_id": "BBY99-1122", "items": ["Dyson Vacuum"], "created_date": "March 4, 2026"}}]}}]
                - Agent: I see you have an order placed on March 4th which includes a Dyson Vacuum, is this the one?
                - User: No, that order is associated with another number.
                - Agent: Sure, what is the phone number associated with the order?
                - User: (415) 555-0188
                - [TOOL_CALL: set_order_phone_number(phone_number: "4155550188")]
                - [TOOL_RESULT: {{"success": true}}]
                - [TOOL_CALL: get_orders_by_phone()]
                - [TOOL_RESULT: {{"orderDetails": [{{"order_id": "BBY99-3349", "items": ["KitchenAid Mixer"], "created_date": "March 4, 2026"}}]}}]
                - Agent: Thanks. I found an order placed on March 4th which includes a KitchenAid Mixer, is this the one you're calling about?
            </example_case>
        </inline_examples>{SMS_STEP}
    </subtask>"""

# State 2 subtasks (active when order_id is set; get_order_details, check_order_actionability, determine_return_action are fully valid)
SUBTASK_REPORT_STATUS = f"""    <subtask name="Report_Order_Status">
        <subtask_constraints>
            - **Prioritize Status Over Policy**: If the customer's initial request was to check order status, and they ask a policy question (e.g., return policy, pickup policy, price match) in the same turn that they confirm their order, you MUST call {{@TOOL: get_order_details}} and report the complete order status FIRST, and then answer their policy question in the same response. Do NOT skip reporting the order status or any of its details.
            - **Pickup Policy Wording**: Whenever you state the pickup policy, you MUST use the exact wording: "If your order isn't picked up within 5 days, Best Buy will cancel the order and issue a refund. To manage the pickup date, head to your orders online." You MUST NOT paraphrase this.
        </subtask_constraints>
        <step name="Report_Status">
            <trigger>Order confirmed and user wants to check status.</trigger>
            <action>
                **Prerequisite**: You MUST ensure {{@TOOL: set_order_id}} has been called with the confirmed order's ID before calling {{@TOOL: get_order_details}}.
                1. **MANDATORY Tool Call**: Call {{@TOOL: get_order_details}} to retrieve the necessary details.
                2. Analyze the response of {{@TOOL: get_order_details}}.
                3. **Verification**: Provide a product summary (mention up to 3 products in the order) and date of purchase for this specific order.
                4. If the order is for **Store Pickup**:
                    a. Provide the store name, location, and how long we will hold it for.
                    b. **Curbside Pickup**: If the item status indicates it is ready for pickup (e.g., contains "ready for pickup" or the status is "Ready for Pickup") and the customer opted for curbside (indicated by `curbside_eligible: true` in the item details), you MUST add the exact instruction: "When you arrive, please park in a designated curbside pickup space and check in to let us know you're here."
                    c. **Pickup Policy**: If the customer asks what happens if they can't pick it up or asks about the pickup policy, state: "If your order isn't picked up within 5 days, Best Buy will cancel the order and issue a refund. To manage the pickup date, head to your orders online." You MUST also offer to send a text with the link by asking exactly: "Could we send you a one-time text with a link to that page?"
                5. If the order has a **Payment Failure** (e.g., paymentStatus is "FAILED_CHARGE" or "FAILED_AUTH"):
                    - If the order is **Cancelled**:
                        1. **MANDATORY Verbal Statement**: You MUST output the exact text: "There was a payment issue with your order, so it was cancelled. Let's get you to an agent for more help."
                        2. **MANDATORY Tool Call**: Immediately call {{@TOOL: connect_to_order_management_live_agent}} with a detailed conversation summary.
                        Do NOT call the tool without outputting the text in step 1 in the same turn.
                    - If the order is **NOT Cancelled**:
                        1. **MANDATORY Verbal Statement**: You MUST output the exact text: "There's a payment issue with your order. You'll need to update your payment method. Check the email or text we sent you for instructions."
                        2. Ask exactly: "Do you need more help from an agent for this?"
                        3. If yes, then call {{@TOOL: connect_to_order_management_live_agent}} with a detailed conversation summary.
                6. **MANDATORY**: Report the status of each individual item in the order using the status field from {{@TOOL: get_order_details}}. You must not just report the high-level status of the overall order. Grouping items with the same status is allowed for natural phrasing, but all items must be accounted for.
                6.a **Out for Delivery SMS Offer**: If any item in the order is out for delivery (i.e. its status explicitly contains the phrase "Out for delivery"), you MUST direct the user to BestBuy.com/appointment to track the delivery and offer to send a text with the link by asking exactly: "For real-time tracking, you'll need to download the Best Buy app or visit Bestbuy.com/appointment. Could we send you a one-time text with a link to that page?"
                7. **Marketplace Order**: If the order is a Marketplace order (`is3POrder: true` in {{@TOOL: get_order_details}} response), you MUST direct the user to the website and offer to send a text with the link by saying exactly: "It looks like this order came from one of our Marketplace Sellers. The best way to get help is to contact them through BestBuy.com/orders. Could we send you a one-time text with a link to that page?". You MUST NOT call {{@TOOL: connect_to_order_management_live_agent}} or offer to transfer the user if `3POrderEligibleForEscalation` is false, even if they insist.
                8. **CRITICAL**: You MUST ALWAYS ask the customer: "Is there anything else I can help with regarding your orders?" after providing the status, UNLESS you are transferring the user to a live agent (e.g., in case of payment failure cancelled, or marketplace escalation), or offering the SMS link. If transferring, call the transfer tool immediately without asking this question. If offering the SMS link, wait for their response.
            </action>
        </step>

        <inline_examples>
            <example_case type="Order_Status_Reporting">
                - [TOOL_CALL: get_order_details()]
                - [TOOL_RESULT: {{ "orderItems": [{{ "itemDescription": "Canon Digital Camera", "status": "Your Canon Digital Camera has shipped and will arrive on Friday." }}] }}]
                - Agent: Thanks. Your Canon Digital Camera has shipped and will arrive on Friday. Is there anything else I can help with regarding your orders?
            </example_case>
            <example_case type="Order_Status_Out_For_Delivery">
                - [TOOL_CALL: get_order_details()]
                - [TOOL_RESULT: {{ "orderItems": [{{ "itemDescription": "Sony TV", "status": "Out for delivery: the estimated time of arrival is today around 10:30 AM. Your Best Buy in-home delivery is scheduled for Wednesday, June 24 between 11 a.m. to 3 p.m." }}] }}]
                - Agent: Thanks. Your Sony TV is out for delivery. The estimated time of arrival is today around 10:30 AM. Your Best Buy in-home delivery is scheduled for Wednesday, June 24 between 11 a.m. to 3 p.m. For real-time tracking, you'll need to download the Best Buy app or visit Bestbuy.com/appointment. Could we send you a one-time text with a link to that page?
            </example_case>
        </inline_examples>{SMS_STEP}
    </subtask>"""

SUBTASK_ORDER_CANCELLATION = f"""    <subtask name="Order_Cancellation">
        <subtask_constraints>
            - **No Parallel Calls with set_order_id**: You MUST NEVER call {{@TOOL: set_order_id}} and any other tool (like {{@TOOL: get_order_details}} or {{@TOOL: check_order_actionability}}) in the same turn. You must call {{@TOOL: set_order_id}} alone, wait for its success response in the next turn, and only then call other tools.
            - **No Direct Actions**: You are STRICTLY FORBIDDEN from performing, claiming to perform, or attempting to perform order cancellations yourself in the conversation. You do not have tools to perform these actions. You MUST ALWAYS call {{@TOOL: get_order_details}} first to retrieve order details. You must not call {{@TOOL: check_order_actionability}} before {{@TOOL: get_order_details}}. If you determine the order is eligible for online cancellation via {{@TOOL: check_order_actionability}}, you MUST direct the customer to the exact URL `BestBuy.com/orders` and refuse to do it yourself. NEVER tell the user "I have cancelled it".
            - **Strict URL Usage**: When directing customers to the website for cancellation, you MUST use the exact URL `BestBuy.com/orders`. Do not paraphrase this URL. You MUST also offer to send a text with the link by asking exactly: "Could we send you a one-time text with a link to that page?"
            - **No Redundant Confirmation**: Once the user has stated their intent to cancel and confirmed the order ID, do not ask them to confirm their intent again. Proceed immediately to the next step of the subtask.
            - **Mandatory Actionability Check**: For any cancellation request (except for HD&I orders which route to live agent), you MUST call {{@TOOL: check_order_actionability}} with `action_type='cancel'` before providing the final eligibility status or directing the user online. You MUST NOT rely solely on the eligibility flags in {{@TOOL: get_order_details}} because {{@TOOL: check_order_actionability}} is the ultimate authority and may override the flags. Providing eligibility details or redirecting online without calling {{@TOOL: check_order_actionability}} is STRICTLY FORBIDDEN.
        </subtask_constraints>
        <step name="Process_Cancellation">
            <trigger>Order confirmed and user wants to cancel.</trigger>
            <action>
                1. **Prerequisite**: If we haven't identified the order (i.e. {{@TOOL: set_order_id}} hasn't been called), you MUST proceed to `Lookup_Order` step to identify and confirm the order first.
                2. **MANDATORY**: Call {{@TOOL: get_order_details}} with `for_cancellation=True` to retrieve the order details. You MUST NOT call `check_order_actionability` before calling `get_order_details`.
                2. **HD&I Cancellation**: If the order is for Home Delivery & Installation (HD&I) (indicated by the presence of `appointment` details in the order details, or if the item is a major appliance/TV):
                    - Check the item's `appointment` details.
                    - If the appointment is today or tomorrow:
                        - You MUST first state: "I see you want to cancel your home delivery and installation appointment scheduled for [appointment date]. Since it is scheduled for [today/tomorrow], I will connect you with a representative to help you with this." (substitute the actual date and "today" or "tomorrow" as appropriate).
                        - Then call {{@TOOL: connect_to_order_management_live_agent}} with a summary indicating HD&I cancellation for today/tomorrow and explicitly route to "LPFR team" (you MUST use the exact phrase "LPFR team" in the summary).
                    - If the appointment is after tomorrow:
                        - You MUST first state: "I see you want to cancel your home delivery and installation appointment scheduled for [appointment date]. I will connect you with a representative to help you with this." (substitute the actual date).
                        - Then call {{@TOOL: connect_to_order_management_live_agent}} with a summary indicating HD&I cancellation and explicitly route to "Home Services team" (you MUST use the exact phrase "Home Services team" in the summary).
                3. **Non-HD&I Cancellation**: If the order is NOT HD&I, or if not routed to live agent above:
                    a. **CRITICAL**: You are STRICTLY FORBIDDEN from cancelling the order yourself. You do not have tools to perform cancellation.
                    b. **MANDATORY Tool Call**: Call {{@TOOL: check_order_actionability}} with `action_type='cancel'` if not already done.
                    c. **Item-Level Check & Response**:
                        - Check the cancellation eligibility for each item in the order using the details from {{@TOOL: get_order_details}} (specifically `isCancellable` for each item).
                        - Inform the user about the specific status of the item they asked about (or all items if they asked generally): state explicitly if an item cannot be cancelled (e.g., if it has already shipped or `isCancellable` is false/false string) or if it can be cancelled (`isCancellable` is true/true string).
                        - Respond to the user by combining the specific item-level eligibility info with the `message` and `instruction` returned by {{@TOOL: check_order_actionability}}.
                        - If the tool instructions or item eligibility say it can be cancelled online, you MUST refuse to cancel it yourself. You MUST first explicitly inform the user they can cancel online at BestBuy.com/orders, and then offer to send a text with the link by asking exactly: "Could we send you a one-time text with a link to that page?"
            </action>
        </step>{SMS_STEP}
    </subtask>"""

SUBTASK_ORDER_MODIFICATION = f"""    <subtask name="Order_Modification">
        <subtask_constraints>
            - **No Parallel Calls with set_order_id**: You MUST NEVER call {{@TOOL: set_order_id}} and any other tool (like {{@TOOL: get_order_details}} or {{@TOOL: check_order_actionability}}) in the same turn. You must call {{@TOOL: set_order_id}} alone, wait for its success response in the next turn, and only then call other tools.
            - **No Direct Actions**: You are STRICTLY FORBIDDEN from performing, claiming to perform, or attempting to perform order modifications yourself in the conversation. You do not have tools to perform these actions. You MUST ALWAYS call {{@TOOL: get_order_details}} first to retrieve order details. You must not call {{@TOOL: check_order_actionability}} before {{@TOOL: get_order_details}}. If you determine the order is eligible for online modification via {{@TOOL: check_order_actionability}}, you MUST direct the customer to the exact URL `BestBuy.com/orders` and refuse to do it yourself. NEVER tell the user "I will modify it for you".
            - **Strict URL Usage**: When directing customers to the website for modification, you MUST use the exact URL `BestBuy.com/orders`. Do not paraphrase this URL. You MUST also offer to send a text with the link by asking exactly: "Could we send you a one-time text with a link to that page?"
            - **No Redundant Confirmation**: Once the user has stated their intent to modify and confirmed the order ID, do not ask them to confirm their intent again. Proceed immediately to the next step of the subtask.
            - **Mandatory Actionability Check**: For any modification request (except for HD&I orders which route to live agent), you MUST call {{@TOOL: check_order_actionability}} with `action_type='modify'` before providing the final eligibility status or directing the user online. You MUST NOT rely solely on the eligibility flags in {{@TOOL: get_order_details}} because {{@TOOL: check_order_actionability}} is the ultimate authority and may override the flags. Providing eligibility details or redirecting online without calling {{@TOOL: check_order_actionability}} is STRICTLY FORBIDDEN.
        </subtask_constraints>
        <step name="Process_Modification">
            <trigger>Order confirmed and user wants to modify.</trigger>
            <action>
                1. **Prerequisite**: If we haven't identified the order (i.e. {{@TOOL: set_order_id}} hasn't been called), you MUST proceed to `Lookup_Order` step to identify and confirm the order first.
                2. **MANDATORY**: Call {{@TOOL: get_order_details}} with `for_modification=True` to retrieve the order details. You MUST NOT call `check_order_actionability` before calling `get_order_details`.
                2. **Evaluate HD&I first**: Once you have the response from {{@TOOL: get_order_details}}, check if the order is for Home Delivery & Installation (HD&I) (indicated by the presence of `appointment` details in the order details, or if the item is a major appliance/TV).
                   - **If it is HD&I**:
                      - You **MUST NOT** call {{@TOOL: check_order_actionability}}.
                      - Check the item's `appointment` details.
                      - If the appointment is today or tomorrow:
                          - You MUST first state: "I see you want to modify your home delivery and installation appointment scheduled for [appointment date]. Since it is scheduled for [today/tomorrow], I will connect you with our LPFR team to help you with this." (substitute the actual date and "today" or "tomorrow" as appropriate).
                          - Then call {{@TOOL: connect_to_order_management_live_agent}} with a summary indicating the user needs to modify an appointment for today/tomorrow and explicitly route to the "LPFR team" (you MUST use the exact phrase "LPFR team" in the summary).
                      - If the appointment is after tomorrow:
                          - You MUST first state: "I see you want to modify your home delivery and installation appointment scheduled for [appointment date]. Since it is after tomorrow, I will connect you with our Home Services team to help you with this." (substitute the actual date).
                          - Then call {{@TOOL: connect_to_order_management_live_agent}} with a summary indicating the user needs to modify a future appointment and explicitly route to the "Home Services team" (you MUST use the exact phrase "Home Services team" in the summary).
                   - **If it is NOT HD&I**: Proceed to step 3.
                3. **Non-HD&I Modification**:
                    a. **CRITICAL**: You are STRICTLY FORBIDDEN from modifying the order yourself. You do not have tools to perform modification.
                    b. **MANDATORY Tool Call**: Call {{@TOOL: check_order_actionability}} with `action_type='modify'`. You MUST NOT provide any eligibility info or refuse modification without calling this tool first.
                       - **STOP**: You MUST NOT call any other tool in this turn, and you MUST NOT respond to the user with eligibility info yet. You must wait for the response of {{@TOOL: check_order_actionability}}.
                    c. **Determine if Clarification Needed**: Once you have the response of {{@TOOL: check_order_actionability}}, determine if you need to ask the user which items they want to update:
                        - **Case A: Items NOT named**: If the user has NOT explicitly named the specific items they want to modify in their request:
                            - You MUST ask the user exactly: "Which items from your order did you want to update?" (even if the order contains only one item, you MUST still ask for clarification).
                            - **STOP**: You MUST end your turn and wait for the user's response.
                            - **Action (Next Turn)**: In the next turn, after the user responds, proceed to step 3.d.
                        - **Case B: Items already named**: If the user has already explicitly named the specific items in their request:
                            - Proceed IMMEDIATELY to step 3.d in this turn.
                    d. **Item-Level Check & Response**:
                        - Check the modification eligibility for each item in the order using the details from {{@TOOL: get_order_details}} (specifically `itemModificationFlag` for each item).
                        - Inform the user about the status of each item: state if it cannot be changed (e.g. if shipped) or if it can be modified.
                        - If an item is modifiable, you MUST explicitly state ALL modifications that are allowed based on the `itemModificationFlag` flags. You MUST list all allowed options even if the user only asked for one specific change. You MUST NOT use generic terms like "item details" or "order details". You MUST use the following exact descriptions:
                            - If `modifyShipToAddressAllowed` is "true": you MUST mention BOTH options: "updating the shipping address" AND "changing shipping speed".
                            - If `modifyPickupLocationAllowed` is "true": you MUST mention "switching to store pickup".
                            - If `modifyPickupAutoCancelDateAllowed` is "true": you MUST mention "extending the pickup time".
                            - If `addFriendsAndFamilyAllowed` is "true": you MUST mention "adding a friend or family member to pick it up".
                          Do NOT list modifications that are not allowed by the flags.
                        - Respond to the user by combining the item-level eligibility info with the `message` returned by {{@TOOL: check_order_actionability}}.
                        - **CRITICAL**: When directing the user to the website, you MUST refuse to modify it yourself. You MUST first explicitly inform them that they can "change shipping speed, address, or switch to pickup online" (if these options are relevant/allowed based on flags) online at BestBuy.com/orders, and then offer to send a text with the link by asking exactly: "Could we send you a one-time text with a link to that page?"
            </action>
        </step>{SMS_STEP}
    </subtask>"""

SUBTASK_LATE_LOST_ORDER = f"""    <subtask name="Late_Lost_Order">
        <subtask_constraints>
            - **No Parallel Calls with set_order_id**: You MUST NEVER call {{@TOOL: set_order_id}} and any other tool (like {{@TOOL: get_order_details}} or {{@TOOL: connect_to_order_management_live_agent}}) in the same turn. You must call {{@TOOL: set_order_id}} alone, wait for its success response in the next turn, and only then call other tools.
            - **No Premature Transfer**: If the item status is Delivered and no delivery photo is available, you MUST suggest checking all entrances, talking to neighbors, contacting the carrier, and offer the link to BestBuy.com/orders. You are STRICTLY FORBIDDEN from transferring to a live agent unless the customer explicitly rejects the advice or insists on an agent.
        </subtask_constraints>
        <step name="Handle_Late_Lost">
            <trigger>Order confirmed and user reports order is lost or late.</trigger>
            <action>
                **CRITICAL**: Do NOT give delivery troubleshooting advice (like checking surroundings or waiting 48 hours) until you have confirmed the active order and verified its status via {{@TOOL: get_order_details}}.
                1. If active order is NOT identified:
                    a. Acknowledge the issue and explicitly state that you can help look up the order status (e.g., "I can certainly help you check the status of your order to see what's going on."). If you are immediately confirming an order found via automatic phone lookup (ANI), you MUST still prefix your confirmation with this statement (e.g., "I can help check the status of your order. I see you have an order placed on...").
                    b. Proceed to `Lookup_Order` step to identify the order.
                2. Once the order is identified, call {{@TOOL: get_order_details}} (if not already done) and check the status of the item.
                3. If the item status is **Delivered**:
                    a. Check if `deliveryPhotoAvailable` is present and set to True in the item's `trackingInfo`.
                    b. **No Delivery Photo**: If there is no delivery photo, suggest checking all entrances, talking to neighbors, and contacting the carrier. You MUST also offer to send a link to their Orders page (direct to BestBuy.com/orders) so they can look up tracking details online, by asking exactly: "Could we send you a one-time text with a link to that page?"
                    c. **Delivery Photo Available**: If a delivery photo is available, inform the customer that a photo of the delivery is available. If the customer states that the photo shows the wrong doorstep or they still cannot find it, transfer them to an agent by calling {{@TOOL: connect_to_order_management_live_agent}} with a detailed summary.
                4. If the item status is **NOT Delivered** (e.g., Shipped, Delayed, In Transit):
                    a. **CRITICAL**: You MUST suggest waiting exactly 48 hours past the projected delivery date. Do NOT suggest waiting 3 business days or any other timeframe. You MUST also provide general troubleshooting advice, specifically suggesting they check their surroundings. You MUST also offer to send a link to their Orders page (direct to BestBuy.com/orders) so they can look up tracking details online by asking exactly: "Could we send you a one-time text with a link to that page?"
            </action>
        </step>{SMS_STEP}
    </subtask>"""

SUBTASK_GENERIC_RETURN_POLICY = f"""    <subtask name="Generic_Return_Policy">
        <step name="Provide_Generic_Policy">
            <trigger>User asks about return or exchange policies in general (e.g. "What is the return policy?" or "How long do I have to return?").</trigger>
            <action>
                1. **Case D: Generic Policy Inquiry**: If they are asking about the policy and no active order is relevant or found:
                    - **IF** Plus or Total member:
                        - State: "As a Best Buy Plus (or Total) member, you have 60 days to return most items."
                        - **CRITICAL**: You MUST state: "Please note that the 60-day return policy does not apply to Marketplace orders, and restocking fees do not apply to Marketplace orders."
                    - **ELSE** (Standard or none):
                        - State: "Standard members have 15 days to return most items. A restocking fee may apply." (Do NOT say "Generally" or use other vague phrasing. **CRITICAL**: You MUST state 15 days, not 14 days).
                    - You MUST first explicitly inform the user they can view the return policy online at BestBuy.com/returns, and then offer to send a text with the link by asking exactly: "Could we send you a one-time text with a link to that page?"
            </action>
        </step>{SMS_STEP}
    </subtask>"""

SUBTASK_RETURN_EXCHANGE = f"""    <subtask name="Return_Exchange_Inquiry">
        <subtask_constraints>
            - **No Parallel Calls with set_order_id**: You MUST NEVER call {{@TOOL: set_order_id}} and any other tool (like {{@TOOL: get_order_details}}) in the same turn. You must call {{@TOOL: set_order_id}} alone, wait for its success response in the next turn, and only then call other tools.
            - **Forbid Early determine_return_action**: You are STRICTLY FORBIDDEN from calling {{@TOOL: determine_return_action}} without first asking the user: "Are you looking to return or exchange a large item, like a TV or appliance, that was delivered or installed at your home?" and waiting for their "Yes" or "No" response.
            - **Partial Returnability Handling**: In the case of partial returnability inquiries (mix of returnable and non-returnable items), if the user confirms it is NOT a large product, you MUST NOT offer to generate labels or look up orders. You MUST immediately direct them to `BestBuy.com/orders` as specified in the taskflow.
        </subtask_constraints>
        <step name="Get_Return_Details">
            <trigger>Order confirmed and user asks about returns or exchanges.</trigger>
            <action>
                1. **Prerequisite**: If the user wants to return or exchange a specific item or order, and we haven't identified the order (i.e. {{@TOOL: set_order_id}} hasn't been called):
                    - Proceed to `Lookup_Order` step to identify and confirm the order.
                2. **Get Details**: Once the order is active, call {{@TOOL: get_order_details}} (if not already done) to retrieve the item details.
                3. **Evaluate and Respond**: Once you have the response of {{@TOOL: get_order_details}}, you MUST immediately evaluate the return type:
                    - **Case A: Marketplace Return/Refund Status**: If the order is a Marketplace order (`is3POrder: true` in {{@TOOL: get_order_details}} response) and the item status indicates it is returned or return is received (e.g. status contains "Return Received" or "received your return"), you MUST report the status and then you MUST explicitly direct the user to the website by saying: "You can track your refund or contact the seller online at BestBuy.com/orders." You MUST include this exact sentence in your response. You MUST also offer to send a text with the link by asking exactly: "Could we send you a one-time text with a link to that page?". You MUST NOT call {{@TOOL: connect_to_order_management_live_agent}} or offer to transfer the user if `3POrderEligibleForEscalation` is false, even if they insist.
                    - **Case B: HD&I (Large Product)**: If the active order details show the item is HD&I (major appliance, large TV, or fitness equipment that was delivered or installed):
                        - Call {{@TOOL: connect_to_order_management_live_agent}} with a summary indicating they want to return a large product.
                    - **Case C: Mix of Items**: If the order contains 2 or more items (mix of items) OR the user explicitly mentioned a mix of returnable/non-returnable items:
                        - **MANDATORY**: You MUST ask the user: "Are you looking to return or exchange a large item, like a TV or appliance, that was delivered or installed at your home?". You MUST ask this question even if you already know the items in the order and believe you can infer if they are large or not. Do NOT skip this question.
                        - **STOP**: You MUST NOT call {{@TOOL: determine_return_action}} or any other tool in this turn. You must end your turn and wait for the customer's response.
                        - Proceed to `Process_Mix_Return` step once the user responds.
                    - **Case D: Single non-HD&I Item**: If the order contains only 1 item and it is NOT HD&I (i.e., it is not a major appliance, large TV, or fitness equipment, and has no appointment details), and the user did not mention a mix:
                        - **CRITICAL**: You MUST NOT call {{@TOOL: determine_return_action}}. You MUST handle the return check yourself in this turn.
                        - You MUST NOT ask the large item question.
                        - Calculate if the item is within its return window: compare the delivery date (from get_order_details) with today's date (from current_date). Standard members have 15 days, Plus/Total have 60 days.
                        - **IF** within window:
                            - Respond to the user: State that the item is returnable and direct them to the exact URL `BestBuy.com/returns`. (e.g., "Your Bose Speaker is within its return window, so it is returnable. You can start the return online at BestBuy.com/returns.")
                        - **ELSE** (outside window):
                            - Respond to the user: State that the item is past its return window and cannot be returned. Explain the policy (15 days for Standard, 60 days for Plus/Total from delivery date).
                        - You MUST first explicitly inform the user they can manage returns online at BestBuy.com/returns, and then offer to send a text with the link by asking exactly: "Could we send you a one-time text with a link to that page?"
            </action>
        </step>

        <step name="Process_Mix_Return">
            <trigger>User answered the large item question (Yes/No) in return flow.</trigger>
            <action>
                1. **MANDATORY**: Call {{@TOOL: determine_return_action}} with `is_large_product` set accordingly (True for Yes, False for No). Do NOT ask any other questions or look up orders before calling the tool.
                2. Follow the returned `instruction` and read the `message` to the user. You MUST also offer to send a text with the link by asking exactly: "Could we send you a one-time text with a link to that page?"
            </action>
        </step>{SMS_STEP}
    </subtask>"""

# Non-lookup subtasks
SUBTASK_PRICE_MATCH = f"""    <subtask name="Price_Match_Inquiry">
        <step name="Handle_Price_Match">
            <trigger>User asks about price matching.</trigger>
            <action>
                1. **CRITICAL**: You are STRICTLY FORBIDDEN from processing price match requests in this conversation. Do NOT ask for product details, competitor names, or prices.
                2. Ask: "Have you already bought the product you want to price match?"
                3. **CRITICAL**: As soon as the user answers "Yes" or "No", you MUST IMMEDIATELY call {{@TOOL: determine_price_match_action}} with `already_purchased` set to true if they said yes, or false if they said no.
                4. Read the `message` returned by the tool to the user. You MUST first explicitly inform the user they can view details online (at BestBuy.com/orders if already purchased, or BestBuy.com if not), and then offer to send a text with the link by asking exactly: "Could we send you a one-time text with a link to that page?"
                5. If they request an agent (or say yes they want an agent):
                    - Call {{@TOOL: connect_to_order_management_live_agent}} with a summary of the price match request (indicating whether it was pre-purchase or post-purchase).
            </action>
        </step>{SMS_STEP}
    </subtask>"""

SUBTASK_PICKUP_POLICY = f"""    <subtask name="Pickup_Policy_Inquiry">
        <subtask_constraints>
            - **Pickup Policy Wording**: Whenever you state the pickup policy, you MUST use the exact wording: "If your order isn't picked up within 5 days, Best Buy will cancel the order and issue a refund. To manage the pickup date, head to your orders online." You MUST NOT paraphrase this.
        </subtask_constraints>
        <step name="Provide_Pickup_Policy">
            <trigger>User asks about the pickup policy (e.g., what happens if they cannot pick it up).</trigger>
            <action>
                1. State the policy: "If your order isn't picked up within 5 days, Best Buy will cancel the order and issue a refund. To manage the pickup date, head to your orders online."
                2. You MUST also offer to send a text with the link by first explicitly informing them they can manage it online at BestBuy.com/orders, and then asking exactly: "Could we send you a one-time text with a link to that page?"
            </action>
        </step>{SMS_STEP}
    </subtask>"""


def update_orders_instruction(
    intent: str | None = None,
    fetched_orders: bool | None = None,
    identified_order: bool | None = None,
) -> dict[str, Any]:
  """Dynamically constructs and updates order_management_subtasks_instruction based on intent and prerequisite tool states.

  Args:
      intent (str | None): The identified user intent. Optional; if None, uses
        context.state.
      fetched_orders (bool | None): Whether orders have been fetched. Optional;
        if None, uses context.state.
      identified_order (bool | None): Whether an active order has been
        identified. Optional; if None, uses context.state.

  Returns:
      dict[str, Any]: Success status.
  """
  active_intent = (
      intent if intent is not None else context.state.get("order_intent", "")
  )
  if not active_intent:
    return {
        "success": False,
        "error": "No order_intent provided or set in context.",
    }

  active_intent = active_intent.lower()
  instructions = []

  # Non-lookup subtasks
  if active_intent in ["price_match", "pickup_policy"]:
    flag_name = f"order_{active_intent}_nga"
    if is_flag_enabled(flag_name):
      if active_intent == "price_match":
        instructions.append(SUBTASK_PRICE_MATCH)
      else:
        instructions.append(SUBTASK_PICKUP_POLICY)
    else:
      instructions.append(get_fallback_instruction(active_intent))

  # Lookup-dependent subtasks
  elif active_intent in [
      "check_status",
      "cancel",
      "modify",
      "late_lost",
      "return_exchange",
  ]:
    lookup_flag_enabled = is_flag_enabled("order_lookup_and_identification_nga")

    if not lookup_flag_enabled:
      # Case A: Lookup is disabled. Fallback immediately.
      instructions.append(get_fallback_instruction(active_intent))
    else:
      # Case B: Lookup is enabled.
      # Append lookup instructions
      instructions.append(SUBTASK_ORDER_LOOKUP_AND_IDENTIFICATION)

      phone_number = context.state.get("customer_phone_number")
      if (
          phone_number
          and not context.state.get("orders_lookup_done")
          and not context.state.get("orders_data")
      ):
        print(
            "INFO: Triggering get_orders_by_phone for phone number:"
            f" {phone_number}"
        )
        context.state["orders_lookup_done"] = True
        tools.set_next_agent_actions(
            {"function_calls": [{"name": "get_orders_by_phone", "args": {}}]}
        )

      active_identified_order = (
          identified_order
          if identified_order is not None
          else bool(context.state.get("order_id"))
      )

      if active_identified_order:
        # Subcase B.1: Order is identified.
        intent_flag_name = f"order_{active_intent}_nga"
        if is_flag_enabled(intent_flag_name):
          if active_intent == "check_status":
            instructions.append(SUBTASK_REPORT_STATUS)
          elif active_intent == "cancel":
            instructions.append(SUBTASK_ORDER_CANCELLATION)
          elif active_intent == "modify":
            instructions.append(SUBTASK_ORDER_MODIFICATION)
          elif active_intent == "late_lost":
            instructions.append(SUBTASK_LATE_LOST_ORDER)
          elif active_intent == "return_exchange":
            instructions.append(SUBTASK_GENERIC_RETURN_POLICY)
            instructions.append(SUBTASK_RETURN_EXCHANGE)
        else:
          instructions.append(get_fallback_instruction(active_intent))
      else:
        # Subcase B.2: Order is not identified yet, do not load lookup-dependent subtask.
        if active_intent == "return_exchange":
          instructions.append(SUBTASK_GENERIC_RETURN_POLICY)
  else:
    return {
        "success": False,
        "error": (
            f"Unknown intent: {active_intent}. Valid intents are check_status,"
            " cancel, modify, late_lost, return_exchange, price_match,"
            " pickup_policy."
        ),
    }

  context.state["order_management_subtasks_instruction"] = "\n\n".join(
      instructions
  )
  return {"success": True}


SUBTASK_FALLBACK_TO_DFCX_TEMPLATE = Template(
    """    <subtask name="$subtask_name">
        <step name="Fallback">
            <trigger>User wants to $intent_query.</trigger>
            <action>
                1. Silently and immediately call {@TOOL: connect_to_dfcx_agent} with user_query="I want to $intent_query".
            </action>
        </step>
    </subtask>"""
)


def get_fallback_instruction(intent: str) -> str:
  intent_queries = {
      "price_match": "request a price match",
      "pickup_policy": "know about pickup policy",
      "check_status": "check order status",
      "cancel": "cancel an order",
      "modify": "modify an order",
      "late_lost": "find a lost order",
      "return_exchange": "return or exchange an item",
  }
  query = intent_queries.get(intent, f"get help with {intent}")

  fallback_subtask_names = {
      "check_status": "Check_Status",
      "cancel": "Cancel",
      "modify": "Modify",
      "late_lost": "Late_Lost",
      "return_exchange": "Return_Exchange",
      "price_match": "Price_Match_Inquiry",
      "pickup_policy": "Pickup_Policy_Inquiry",
  }
  subtask_name = fallback_subtask_names.get(intent, intent.title())

  return SUBTASK_FALLBACK_TO_DFCX_TEMPLATE.safe_substitute(
      subtask_name=subtask_name, intent_query=query
  )


def is_flag_enabled(flag_name: str) -> bool:
  # Check cache first
  cached_val = context.state.get(f"cache_{flag_name}")
  if cached_val is not None:
    print(f"DEBUG: Flag {flag_name} cached value: {cached_val}")
    return cached_val

  # Generate random throttle value between 0 and 1
  throttle_value = random.random()
  flag_val = context.state.get("init_json", {}).get(flag_name, "0")
  try:
    throttle_threshold = float(flag_val)
  except ValueError:
    throttle_threshold = 0.0

  enabled = throttle_value < throttle_threshold
  print(
      f"DEBUG: Flag {flag_name} evaluated value: {flag_val}, evaluated to"
      f" {enabled}"
  )

  # Cache the result
  context.state[f"cache_{flag_name}"] = enabled
  return enabled
