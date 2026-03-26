"""Test script for Stage 2 multi-turn conversation."""
from smart_customer_service.graph import create_conversation_graph, run_conversation_turn
from smart_customer_service.config import Config


def test_order_query_with_missing_order_id():
    """Test order query flow where user doesn't provide order_id initially."""
    print("\n" + "="*60)
    print("Test 1: Order Query with Missing Order ID")
    print("="*60)

    try:
        Config.validate()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return

    graph = create_conversation_graph()

    # Initial state
    state = {
        "messages": [],
        "intent": None,
        "parameters": {},
        "tool_result": None,
        "waiting_for_parameter": None,
        "completed": False,
    }

    # Turn 1: User says "查订单" without order_id
    print("\n👤 User: 查订单")
    state = run_conversation_turn(graph, state, "查订单")
    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        print(f"🤖 Bot: {last_msg.content}")
        print(f"   State: intent={state.get('intent')}, waiting_for={state.get('waiting_for_parameter')}")

    # Turn 2: User provides order_id
    print("\n👤 User: ORD001")
    state = run_conversation_turn(graph, state, "ORD001")
    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        print(f"🤖 Bot: {last_msg.content}")
        print(f"   State: completed={state.get('completed')}, tool_result={bool(state.get('tool_result'))}")

    print("\n✅ Test 1 completed\n")


def test_refund_request():
    """Test refund request flow."""
    print("\n" + "="*60)
    print("Test 2: Refund Request")
    print("="*60)

    try:
        Config.validate()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return

    graph = create_conversation_graph()

    state = {
        "messages": [],
        "intent": None,
        "parameters": {},
        "tool_result": None,
        "waiting_for_parameter": None,
        "completed": False,
    }

    # Turn 1: User wants refund
    print("\n👤 User: 我要申请退款")
    state = run_conversation_turn(graph, state, "我要申请退款")
    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        print(f"🤖 Bot: {last_msg.content}")
        print(f"   State: intent={state.get('intent')}, waiting_for={state.get('waiting_for_parameter')}")

    # Turn 2: Provide order_id
    print("\n👤 User: ORD003")
    state = run_conversation_turn(graph, state, "ORD003")
    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        print(f"🤖 Bot: {last_msg.content}")
        print(f"   State: completed={state.get('completed')}")

    print("\n✅ Test 2 completed\n")


def test_direct_order_query():
    """Test order query with order_id provided directly."""
    print("\n" + "="*60)
    print("Test 3: Direct Order Query (with order_id)")
    print("="*60)

    try:
        Config.validate()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return

    graph = create_conversation_graph()

    state = {
        "messages": [],
        "intent": None,
        "parameters": {},
        "tool_result": None,
        "waiting_for_parameter": None,
        "completed": False,
    }

    # Single turn: User provides everything
    print("\n👤 User: 查询订单 ORD002")
    state = run_conversation_turn(graph, state, "查询订单 ORD002")
    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        print(f"🤖 Bot: {last_msg.content}")
        print(f"   State: intent={state.get('intent')}, completed={state.get('completed')}")

    print("\n✅ Test 3 completed\n")


if __name__ == "__main__":
    print("Starting Stage 2 Tests")
    print("="*60)

    try:
        test_order_query_with_missing_order_id()
        test_refund_request()
        test_direct_order_query()

        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("="*60)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
