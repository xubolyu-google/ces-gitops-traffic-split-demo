# pylint: disable=missing-function-docstring,missing-class-docstring,missing-module-docstring,invalid-name,undefined-variable,line-too-long

SERVICE_CONTEXT_INSTRUCTION = """
      <step name="Create_and_Get_Service_Context">
        <trigger>Immediately on entering `Determine_Service_Entitlement`.</trigger>
        <action>
        1. Silently call `{@TOOL: create_and_get_service_context}` and immediately transition to the `Process_Entitlement_Result` step.
        </action>
      </step>
      <step name="Process_Entitlement_Result">
        <trigger>After the `create_and_get_service_context` tool has been executed.</trigger>
        <action>
        1. **Carefully analyze the `{@TOOL: create_and_get_service_context}` tool response.**
           The response is a list of service paths, each with a `type`, `ranking`, and `status`.

        2. **Check if the response contains at least one service path:**
           - If the response is **empty or has no paths**:
             - Offer to transfer the user to a live agent and then silently and immediately call the {@TOOL: connect_to_computing_service_live_agent} tool.

        3. **If paths exist**, set a pointer to the first (highest-ranked) path.
           - Silently call `{@TOOL: present_service_path_option}` with the current path's `type`.
           - The tool returns a `phrase` and `requires_confirmation`.
           - Say the `phrase` exactly as returned. Do NOT use internal labels or tool names with the user.
           - If `requires_confirmation` is **true**:
             **STOP here and wait for the user's response. Do NOT transition yet.**
             - **If the user DECLINES:**
               Move the pointer to the next ranked path.
               - If another path exists, repeat step 3 with the next option.
               - If no more paths remain, proceed to step 5.
             - **If the user AGREES:** Make a note of the type and link for the selected option and proceed to step 4.
           - If `requires_confirmation` is **false**: The phrase is informational only. Proceed directly to step 4 with this option's type and link.
        4. **Route:** Silently call `{@TOOL: check_service_entitlement}` with the known values of `type` and `link`.
        5. **If the user declines ALL available options:**
           - Do NOT offer any additional services, appointments, or alternatives that were not in the original paths list.
           - Silently and immediately call the {@TOOL: call_wrapup} tool.
        </action>
      </step>
"""


def before_agent_callback(
    callback_context: CallbackContext,
) -> Optional[Content]:
  variables = callback_context.variables
  if not variables.get("determine_service_context_instruction"):
    variables["determine_service_context_instruction"] = (
        SERVICE_CONTEXT_INSTRUCTION
    )
