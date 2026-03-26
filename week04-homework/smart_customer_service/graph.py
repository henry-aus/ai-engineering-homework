"""LangGraph conversation graph for multi-turn dialogues."""
from typing import TypedDict, Annotated, Literal, Optional, Dict, Any, List
from datetime import datetime
import json

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from .config import Config
from .tools import TOOLS, query_order, process_refund, issue_invoice


# State schema
class ConversationState(TypedDict):
    """State for the conversation graph."""
    messages: Annotated[List[BaseMessage], add_messages]
    intent: Optional[str]
    parameters: Dict[str, Any]
    tool_result: Optional[Dict[str, Any]]
    waiting_for_parameter: Optional[str]
    completed: bool


# Initialize LLM
def get_llm():
    """Get configured LLM instance."""
    Config.validate()
    return ChatOpenAI(
        model=Config.OPENAI_MODEL,
        api_key=Config.OPENAI_API_KEY,
        temperature=0,
    )


# Node: Extract intent and parameters
def extract_intent(state: ConversationState) -> ConversationState:
    """Extract user intent and parameters from the latest message."""
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""
    current_intent = state.get("intent")
    waiting_for = state.get("waiting_for_parameter")

    current_date = datetime.now().strftime("%Y-%m-%d")

    # Build context about current state
    state_context = ""
    if current_intent and waiting_for:
        state_context = f"\n当前对话状态：正在进行 {current_intent}，等待用户提供 {waiting_for}"

    prompt = f"""今天的日期是：{current_date}

你是一个智能客服助手。分析用户的最新消息，提取意图和参数。
{state_context}

用户历史对话：
{chr(10).join([f"{m.type}: {m.content}" for m in messages[-5:]])}

**重要**：如果当前正在等待用户提供某个参数（如订单号），且用户的消息看起来是在回答这个问题，则保持当前意图不变，只提取参数。

请分析最新消息并输出 JSON：
{{
  "intent": "order_query" | "refund_request" | "invoice_request" | "general",
  "parameters": {{
    "order_id": "订单号（如果提到）",
    "reason": "退款原因（如果是退款申请）",
    "invoice_type": "发票类型（个人/企业）",
    "invoice_title": "发票抬头（企业发票需要）",
    "date_mentioned": "日期（YYYY-MM-DD格式）"
  }},
  "confidence": "high" | "medium" | "low"
}}

示例：
用户："查一下我的订单"
输出：{{"intent": "order_query", "parameters": {{}}, "confidence": "high"}}

用户："ORD001"（当前正在进行 order_query，等待 order_id）
输出：{{"intent": "order_query", "parameters": {{"order_id": "ORD001"}}, "confidence": "high"}}

用户："我要申请退款"
输出：{{"intent": "refund_request", "parameters": {{}}, "confidence": "high"}}

用户："ORD003"（当前正在进行 refund_request，等待 order_id）
输出：{{"intent": "refund_request", "parameters": {{"order_id": "ORD003"}}, "confidence": "high"}}

只输出JSON，不要其他内容。
"""

    llm = get_llm()
    try:
        response = llm.invoke([SystemMessage(content=prompt)])
        result = json.loads(response.content)

        # Merge new parameters with existing ones
        existing_params = state.get("parameters", {})
        new_params = result.get("parameters", {})
        merged_params = {**existing_params, **{k: v for k, v in new_params.items() if v}}

        # If we're waiting for a parameter and got something, prefer keeping current intent
        new_intent = result.get("intent")
        if current_intent and waiting_for and new_params.get(waiting_for):
            # User is providing the missing parameter, keep the intent
            new_intent = current_intent

        return {
            **state,
            "intent": new_intent or current_intent or "general",
            "parameters": merged_params,
        }
    except Exception as e:
        print(f"⚠️  Intent extraction failed: {e}")
        return {
            **state,
            "intent": state.get("intent", "general"),
            "parameters": state.get("parameters", {}),
        }


# Node: Check if we have all required parameters
def check_parameters(state: ConversationState) -> ConversationState:
    """Check if we have all required parameters for the intent."""
    intent = state.get("intent")
    parameters = state.get("parameters", {})

    # Define required parameters for each intent
    required_params = {
        "order_query": ["order_id"],
        "refund_request": ["order_id"],  # reason is optional
        "invoice_request": ["order_id"],  # others are optional
    }

    if intent not in required_params:
        return {**state, "waiting_for_parameter": None}

    # Check which parameters are missing
    required = required_params[intent]
    for param in required:
        if param not in parameters or not parameters[param]:
            return {**state, "waiting_for_parameter": param}

    return {**state, "waiting_for_parameter": None}


# Node: Ask for missing parameters
def ask_for_parameter(state: ConversationState) -> ConversationState:
    """Ask user for missing parameter."""
    waiting_for = state.get("waiting_for_parameter")
    intent = state.get("intent")

    # Generate question based on missing parameter
    questions = {
        "order_id": "请提供您的订单号，格式如：ORD001",
        "reason": "请问退款的原因是什么？",
        "invoice_type": "请问需要开具个人发票还是企业发票？",
        "invoice_title": "请提供企业发票的抬头名称",
    }

    question = questions.get(waiting_for, f"请提供 {waiting_for}")

    return {
        **state,
        "messages": state["messages"] + [AIMessage(content=question)],
    }


# Node: Call tool
def call_tool(state: ConversationState) -> ConversationState:
    """Call the appropriate tool based on intent."""
    intent = state.get("intent")
    parameters = state.get("parameters", {})

    try:
        if intent == "order_query":
            result = query_order.invoke({"order_id": parameters.get("order_id")})
        elif intent == "refund_request":
            result = process_refund.invoke({
                "order_id": parameters.get("order_id"),
                "reason": parameters.get("reason", "")
            })
        elif intent == "invoice_request":
            result = issue_invoice.invoke({
                "order_id": parameters.get("order_id"),
                "invoice_type": parameters.get("invoice_type", "个人"),
                "invoice_title": parameters.get("invoice_title", "")
            })
        else:
            result = {"error": "Unknown intent"}

        return {
            **state,
            "tool_result": result,
        }
    except Exception as e:
        return {
            **state,
            "tool_result": {"error": str(e)},
        }


# Node: Generate response
def generate_response(state: ConversationState) -> ConversationState:
    """Generate final response based on tool result."""
    tool_result = state.get("tool_result")
    intent = state.get("intent")

    if not tool_result:
        response = "抱歉，我没有理解您的需求。"
    elif "error" in tool_result:
        response = f"❌ {tool_result.get('message', tool_result.get('error'))}"
    else:
        # Format response based on intent and result
        if intent == "order_query":
            if "status" in tool_result:
                response = f"""📦 订单信息查询成功

订单号：{tool_result['order_id']}
订单状态：{tool_result['status']}
下单时间：{tool_result['create_time']}
订单金额：¥{tool_result['total_amount']:.2f}

📍 物流信息：
物流公司：{tool_result['logistics']['company']}
运单号：{tool_result['logistics']['tracking_number']}
当前位置：{tool_result['logistics']['current_location']}
{'预计送达：' + tool_result['logistics']['estimated_delivery'] if 'estimated_delivery' in tool_result['logistics'] else ''}
"""
            else:
                response = "未找到订单信息"

        elif intent == "refund_request":
            if tool_result.get("success"):
                response = f"""✅ {tool_result['message']}

退款单号：{tool_result['refund_id']}
退款金额：¥{tool_result['refund_amount']:.2f}
处理状态：{tool_result['status']}
预计到账：{tool_result['estimated_time']}
"""
            else:
                response = f"❌ {tool_result.get('message', '退款申请失败')}"

        elif intent == "invoice_request":
            if tool_result.get("success"):
                response = f"""✅ {tool_result['message']}

发票号：{tool_result['invoice_id']}
发票类型：{tool_result['invoice_type']}
发票抬头：{tool_result['invoice_title']}
发票金额：¥{tool_result['amount']:.2f}
下载链接：{tool_result['download_url']}
"""
            else:
                response = f"❌ {tool_result.get('message', '发票开具失败')}"
        else:
            response = json.dumps(tool_result, ensure_ascii=False, indent=2)

    return {
        **state,
        "messages": state["messages"] + [AIMessage(content=response)],
        "completed": True,
    }


# Routing logic
def should_continue(state: ConversationState) -> Literal["check_params", "end"]:
    """Decide whether to continue or end."""
    if state.get("completed"):
        return "end"
    return "check_params"


def route_after_check(state: ConversationState) -> Literal["ask", "call_tool"]:
    """Route after parameter check."""
    if state.get("waiting_for_parameter"):
        return "ask"
    return "call_tool"


# Build the graph
def create_conversation_graph():
    """Create and compile the conversation graph."""
    workflow = StateGraph(ConversationState)

    # Add nodes
    workflow.add_node("extract_intent", extract_intent)
    workflow.add_node("check_params", check_parameters)
    workflow.add_node("ask", ask_for_parameter)
    workflow.add_node("call_tool", call_tool)
    workflow.add_node("generate_response", generate_response)

    # Set entry point
    workflow.set_entry_point("extract_intent")

    # Add edges
    workflow.add_edge("extract_intent", "check_params")
    workflow.add_conditional_edges(
        "check_params",
        route_after_check,
        {
            "ask": "ask",
            "call_tool": "call_tool",
        }
    )
    workflow.add_edge("ask", END)
    workflow.add_edge("call_tool", "generate_response")
    workflow.add_edge("generate_response", END)

    return workflow.compile()


# Convenience function
def run_conversation_turn(graph, state: ConversationState, user_input: str) -> ConversationState:
    """Run one turn of the conversation."""
    # Add user message to state
    new_state = {
        **state,
        "messages": state.get("messages", []) + [HumanMessage(content=user_input)],
        "completed": False,
    }

    # Run the graph
    result = graph.invoke(new_state)
    return result
