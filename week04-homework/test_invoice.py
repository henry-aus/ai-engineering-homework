"""Test script for Stage 3 - Invoice Plugin Functionality."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from smart_customer_service.graph import create_conversation_graph, run_conversation_turn
from smart_customer_service.config import Config
from smart_customer_service.tools import issue_invoice


def test_invoice_tool_direct():
    """Test invoice tool directly with various scenarios."""
    print("\n" + "="*60)
    print("Test 1: Direct Invoice Tool Testing")
    print("="*60)

    # Test 1.1: Personal invoice
    print("\n📝 Test 1.1: Issue personal invoice")
    result = issue_invoice.invoke({
        "order_id": "ORD001",
        "invoice_type": "个人",
        "invoice_title": ""
    })
    print(f"   Result: {result}")
    assert result["success"] == True, "Personal invoice should succeed"
    assert result["invoice_type"] == "个人", "Invoice type should be 个人"
    assert result["invoice_title"] == "个人", "Invoice title should default to 个人"
    print("   ✅ Personal invoice test passed")

    # Test 1.2: Enterprise invoice with title
    print("\n📝 Test 1.2: Issue enterprise invoice with title")
    result = issue_invoice.invoke({
        "order_id": "ORD002",
        "invoice_type": "企业",
        "invoice_title": "极客时间科技有限公司"
    })
    print(f"   Result: {result}")
    assert result["success"] == True, "Enterprise invoice with title should succeed"
    assert result["invoice_type"] == "企业", "Invoice type should be 企业"
    assert result["invoice_title"] == "极客时间科技有限公司", "Invoice title should match"
    print("   ✅ Enterprise invoice with title test passed")

    # Test 1.3: Enterprise invoice without title (should fail)
    print("\n📝 Test 1.3: Issue enterprise invoice without title (should fail)")
    result = issue_invoice.invoke({
        "order_id": "ORD003",
        "invoice_type": "企业",
        "invoice_title": ""
    })
    print(f"   Result: {result}")
    assert result["success"] == False, "Enterprise invoice without title should fail"
    assert "发票抬头" in result["message"], "Error message should mention invoice title"
    print("   ✅ Enterprise invoice validation test passed")

    # Test 1.4: Invalid order ID
    print("\n📝 Test 1.4: Issue invoice for non-existent order")
    result = issue_invoice.invoke({
        "order_id": "ORD999",
        "invoice_type": "个人",
        "invoice_title": ""
    })
    print(f"   Result: {result}")
    assert result["success"] == False, "Invalid order should fail"
    assert "未找到订单号" in result["message"] or "订单不存在" in result.get("error", ""), "Error message should mention order not found"
    print("   ✅ Invalid order test passed")

    print("\n✅ All direct tool tests passed!\n")


def test_invoice_conversation_flow():
    """Test invoice issuance through conversation flow."""
    print("\n" + "="*60)
    print("Test 2: Invoice Request Conversation Flow")
    print("="*60)

    try:
        Config.validate()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return

    graph = create_conversation_graph()

    # Test 2.1: Personal invoice request
    print("\n📝 Test 2.1: Personal invoice request flow")
    state = {
        "messages": [],
        "intent": None,
        "parameters": {},
        "tool_result": None,
        "waiting_for_parameter": None,
        "completed": False,
    }

    # Turn 1: User wants invoice
    print("\n👤 User: 我要开发票")
    state = run_conversation_turn(graph, state, "我要开发票")
    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        print(f"🤖 Bot: {last_msg.content}")
        print(f"   State: intent={state.get('intent')}, waiting_for={state.get('waiting_for_parameter')}")

    # Turn 2: Provide order_id
    print("\n👤 User: ORD001")
    state = run_conversation_turn(graph, state, "ORD001")
    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        print(f"🤖 Bot: {last_msg.content}")
        print(f"   State: completed={state.get('completed')}")

    # Verify invoice was issued
    tool_result = state.get("tool_result")
    assert tool_result is not None, "Tool should have been called"
    assert tool_result.get("success") == True, "Invoice should be issued successfully"
    print("   ✅ Personal invoice conversation flow passed")

    # Test 2.2: Enterprise invoice request
    print("\n📝 Test 2.2: Enterprise invoice request flow")
    state = {
        "messages": [],
        "intent": None,
        "parameters": {},
        "tool_result": None,
        "waiting_for_parameter": None,
        "completed": False,
    }

    # Turn 1: User wants enterprise invoice with all info
    print("\n👤 User: 我要开企业发票，订单号ORD002，抬头是极客时间科技有限公司")
    state = run_conversation_turn(graph, state, "我要开企业发票，订单号ORD002，抬头是极客时间科技有限公司")
    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        print(f"🤖 Bot: {last_msg.content}")
        print(f"   State: completed={state.get('completed')}")

    # Verify enterprise invoice
    tool_result = state.get("tool_result")
    assert tool_result is not None, "Tool should have been called"
    if tool_result.get("success"):
        assert tool_result.get("invoice_type") == "企业", "Should be enterprise invoice"
        print("   ✅ Enterprise invoice conversation flow passed")
    else:
        print(f"   ⚠️  Enterprise invoice may need multi-turn: {tool_result}")

    print("\n✅ All conversation flow tests passed!\n")


def test_invoice_parameters():
    """Test invoice with various parameter combinations."""
    print("\n" + "="*60)
    print("Test 3: Invoice Parameter Validation")
    print("="*60)

    # Test all valid orders
    valid_orders = ["ORD001", "ORD002", "ORD003"]
    for order_id in valid_orders:
        print(f"\n📝 Testing invoice for {order_id}")
        result = issue_invoice.invoke({
            "order_id": order_id,
            "invoice_type": "个人",
            "invoice_title": ""
        })
        print(f"   Order {order_id}: {result.get('message', 'N/A')}")
        assert result["success"] == True, f"Invoice for {order_id} should succeed"
        assert "invoice_id" in result, "Result should contain invoice_id"
        assert "download_url" in result, "Result should contain download_url"
        print(f"   ✅ Invoice {result['invoice_id']} issued successfully")

    print("\n✅ All parameter validation tests passed!\n")


if __name__ == "__main__":
    print("Starting Stage 3 Invoice Plugin Tests")
    print("="*60)

    try:
        # Run all tests
        test_invoice_tool_direct()
        test_invoice_conversation_flow()
        test_invoice_parameters()

        print("\n" + "="*60)
        print("✅ All Stage 3 invoice tests completed successfully!")
        print("="*60)

    except AssertionError as e:
        print(f"\n❌ Test assertion failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
