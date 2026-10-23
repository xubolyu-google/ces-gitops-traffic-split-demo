def connect_to_computing_service_live_agent(conversation_summary: str) -> None:
  """Connects the user to a computing service live agent.

  args:
      conversation_summary (str): A detailed summary of the conversation to
      date.
        - FORMAT: Professional, third-person narrative.
        - CONTENT: Include the following ONLY if they have been explicitly 
          disclosed in the conversation:
          1. The specific issue and device details.
          2. Troubleshooting steps attempted during this session and their outcomes.
          3. The immediate trigger for the escalation (e.g., user request, 
             unresolved error, or technical limitation).
          4. Any additional details that the live agent should be aware of.
        - DATA INTEGRITY: Do not infer or hallucinate details (like device 
          models or specific errors) if the user has not provided them. If a 
          category is unknown, omit it.
        - CRITICAL: This is the human agent's first point of context. Accuracy 
          is paramount to avoid making the user repeat themselves.
        - EXAMPLE (Full Context): "User's MacBook Pro is experiencing persistent 
          latency. Guided user through a hard reboot, but performance did not 
          improve. Escalated because user was unable to install the LMI program
          due to a permission error."
        - EXAMPLE (Limited Context): "User reported that their tablet is not
          turning on but did not specify the device. Escalated per user request
          for live assistance."

  Returns:
      None
  """
  call_context = context.state["call_context"]
  call_context["queue"] = "SVC.CPU.______.EN.VCE.ALL"
  classification = context.state.get("computer_troubleshooting_issue_classification")
  if classification == "hardware":
    call_context["callIntent"] = "troubleshooting.hardware"
  elif classification == "software":
    call_context["callIntent"] = "troubleshooting.software"
  else:
    call_context["callIntent"] = "troubleshooting.vague"
  call_context["callerIntentCode"] = "0856"
  # Fetch fresh LMI status directly from the API to avoid stale state
  # (context.state may not reflect changes made by the calling callback)
  lmi_status = context.state.get("lmi_status")
  lmi_id = context.state.get("lmi_session_id")
  if context.state.get("initiated_lmi") and not lmi_id:
    try:
      lmi_status_response = tools.check_lmi_status({}).json()["result"]
      lmi_status = lmi_status_response.get("Status", lmi_status)
      if lmi_status_response.get("ID"):
        lmi_id = lmi_status_response.get("ID")
        context.state["lmi_session_id"] = lmi_id
    except Exception as e:
      print(f"ERROR: Failed to fetch fresh LMI status: {e!r}")
  if context.state.get("initiated_lmi") and lmi_id:
    call_context["lmiSessionId"] = lmi_id
  # LMI funnel tracking for analytics
  lmi_session_id = context.state.get("lmi_session_id")
  call_context["lmiTracking"] = {
      "lmiOffered": bool(context.state.get("lmi_offered")),
      "lmiAccepted": bool(context.state.get("initiated_lmi")),
      "lmiLastStatus": lmi_status or "",
      "lmiSessionId": lmi_id,
      "customerCompletedDownload": lmi_status in (
          "DownloadCompleted", "SessionCreated", "SessionNotCreated"
      ),
      "lmiPin": str(context.state.get("lmi_pin") or ""),
  }
  call_context["conversationSummarization"] = conversation_summary
  call_context["isSummarize"] = True
  call_context["brand"] = context.state.get("brand", "none")
  pre_engagement_data = call_context["preEngagementData"] = {
      "product": {"productType": context.state.get("product_type", "unknown")},
      "issueType": call_context["callIntent"],
  }
  if item_id := context.state.get("item_id"):
    if product := context.state.get("product_by_item_id", {}).get(item_id):
      call_context["brand"] = product.get("brand") or call_context["brand"]
      call_context["sku"] = product.get("skuId")
      call_context["orderNumber"] = product.get("orderNumber")
      pre_engagement_data["product"].update({
          "productName": product.get("productName"),
          "sku": product.get("skuId"),
          "isUnderManufacturerWarranty": product.get(
              "isUnderManufacturerWarranty"
          ),
          "isReturnEligible": product.get("isReturnEligible"),
          "isCoveredByProtectionPlan": product.get("isCoveredByProtectionPlan"),
      })

  # callback will handle the transfer to Twilio (i.e. end the session).
  tools.set_call_context({"call_context": call_context})
  context.state["should_connect_to_twilio_queue_with_response"] = True
  return None
