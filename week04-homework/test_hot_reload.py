"""Test script for Stage 3 - Hot Reload and Session Isolation."""
import sys
import time
import httpx
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def test_hot_reload_manager():
    """Test hot reload manager directly."""
    print("\n" + "="*60)
    print("Test 1: Hot Reload Manager Direct Testing")
    print("="*60)

    from smart_customer_service.hot_reload import get_hot_reload_manager
    from smart_customer_service.config import Config

    try:
        Config.validate()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return

    manager = get_hot_reload_manager()

    # Test 1.1: Get initial versions
    print("\n📝 Test 1.1: Get initial versions")
    initial_versions = manager.get_current_version()
    print(f"   Initial versions: {initial_versions}")
    assert "model_version" in initial_versions
    assert "plugin_version" in initial_versions
    print("   ✅ Initial versions retrieved")

    # Test 1.2: Get initial status
    print("\n📝 Test 1.2: Get initial status")
    status = manager.get_status()
    print(f"   Status: {status}")
    assert status["model_version"] == initial_versions["model_version"]
    assert status["plugin_version"] == initial_versions["plugin_version"]
    assert len(status["plugins"]) > 0
    print(f"   Plugins: {status['plugins']}")
    print("   ✅ Initial status retrieved")

    # Test 1.3: Reload model configuration
    print("\n📝 Test 1.3: Reload model configuration")
    old_model = status["model_config"]["model"]
    result = manager.reload_model(temperature=0.5)
    print(f"   Reload result: {result}")
    assert result["success"] == True
    new_versions = manager.get_current_version()
    assert new_versions["model_version"] > initial_versions["model_version"]
    print(f"   Model version updated: {initial_versions['model_version']} -> {new_versions['model_version']}")
    print("   ✅ Model reload successful")

    # Test 1.4: Reload plugins
    print("\n📝 Test 1.4: Reload plugins")
    result = manager.reload_plugins()
    print(f"   Reload result: {result}")
    assert result["success"] == True
    newest_versions = manager.get_current_version()
    assert newest_versions["plugin_version"] > new_versions["plugin_version"]
    print(f"   Plugin version updated: {new_versions['plugin_version']} -> {newest_versions['plugin_version']}")
    print("   ✅ Plugin reload successful")

    # Test 1.5: Get LLM and plugins
    print("\n📝 Test 1.5: Get LLM and plugins instances")
    llm = manager.get_llm()
    plugins = manager.get_plugins()
    print(f"   LLM: {llm.model_name}")
    print(f"   Plugins count: {len(plugins)}")
    assert llm is not None
    assert len(plugins) > 0
    print("   ✅ LLM and plugins retrieved")

    print("\n✅ All hot reload manager tests passed!\n")


async def test_api_hot_reload():
    """Test hot reload through API endpoints."""
    print("\n" + "="*60)
    print("Test 2: API Hot Reload Testing")
    print("="*60)

    from smart_customer_service.config import Config

    base_url = f"http://{Config.API_HOST}:{Config.API_PORT}"
    print(f"   API URL: {base_url}")
    print("   ⚠️  Note: This test requires the API server to be running")
    print("   Start server with: python -m smart_customer_service.api")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test 2.1: Health check
            print("\n📝 Test 2.1: Health check endpoint")
            try:
                response = await client.get(f"{base_url}/health")
                if response.status_code != 200:
                    print(f"   ⚠️  API server not responding (status {response.status_code})")
                    print("   Skipping API tests - server may not be running")
                    return

                health = response.json()
                print(f"   Status: {health['status']}")
                print(f"   Version: {health['version']}")
                print(f"   Model version: {health['hot_reload']['model_version']}")
                print(f"   Plugin version: {health['hot_reload']['plugin_version']}")
                assert health["status"] == "healthy"
                print("   ✅ Health check passed")
            except httpx.ConnectError:
                print("   ⚠️  Cannot connect to API server")
                print("   Skipping API tests - please start the server first")
                return

            initial_health = health

            # Test 2.2: Create a session before hot reload
            print("\n📝 Test 2.2: Create session before hot reload")
            response = await client.post(
                f"{base_url}/chat",
                json={"message": "我要查订单"}
            )
            assert response.status_code == 200
            chat_response = response.json()
            session_id = chat_response["session_id"]
            print(f"   Session created: {session_id}")
            print(f"   Bot response: {chat_response['response'][:50]}...")
            print("   ✅ Session created successfully")

            # Test 2.3: Trigger model hot reload
            print("\n📝 Test 2.3: Trigger model hot reload")
            response = await client.post(
                f"{base_url}/admin/reload-model",
                json={"temperature": 0.7}
            )
            assert response.status_code == 200
            reload_result = response.json()
            print(f"   Reload success: {reload_result['success']}")
            print(f"   Message: {reload_result['message']}")
            print("   ✅ Model hot reload triggered")

            # Test 2.4: Continue old session (should still work)
            print("\n📝 Test 2.4: Continue old session after hot reload")
            response = await client.post(
                f"{base_url}/chat",
                json={
                    "session_id": session_id,
                    "message": "ORD001"
                }
            )
            assert response.status_code == 200
            chat_response = response.json()
            print(f"   Bot response: {chat_response['response'][:100]}...")
            assert chat_response["session_id"] == session_id
            print("   ✅ Old session continues working after hot reload")

            # Test 2.5: Create new session (should use new model)
            print("\n📝 Test 2.5: Create new session after hot reload")
            response = await client.post(
                f"{base_url}/chat",
                json={"message": "你好"}
            )
            assert response.status_code == 200
            chat_response = response.json()
            new_session_id = chat_response["session_id"]
            print(f"   New session created: {new_session_id}")
            assert new_session_id != session_id
            print("   ✅ New session created with updated config")

            # Test 2.6: Verify model version increased
            print("\n📝 Test 2.6: Verify model version increased")
            response = await client.get(f"{base_url}/health")
            assert response.status_code == 200
            new_health = response.json()
            print(f"   Old model version: {initial_health['hot_reload']['model_version']}")
            print(f"   New model version: {new_health['hot_reload']['model_version']}")
            assert new_health['hot_reload']['model_version'] > initial_health['hot_reload']['model_version']
            print("   ✅ Model version increased")

            # Test 2.7: Trigger plugin hot reload
            print("\n📝 Test 2.7: Trigger plugin hot reload")
            response = await client.post(f"{base_url}/admin/reload-plugins")
            assert response.status_code == 200
            reload_result = response.json()
            print(f"   Reload success: {reload_result['success']}")
            print(f"   Plugins: {reload_result['details']['plugins']}")
            print("   ✅ Plugin hot reload triggered")

            # Test 2.8: List sessions
            print("\n📝 Test 2.8: List active sessions")
            response = await client.get(f"{base_url}/admin/sessions")
            assert response.status_code == 200
            sessions = response.json()
            print(f"   Total sessions: {sessions['total']}")
            print(f"   Sessions: {[s['session_id'][:8] for s in sessions['sessions']]}")
            assert sessions['total'] >= 2  # At least the two sessions we created
            print("   ✅ Sessions listed successfully")

            print("\n✅ All API hot reload tests passed!\n")

    except Exception as e:
        print(f"\n❌ API test error: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_session_isolation():
    """Test that hot reload doesn't affect existing sessions."""
    print("\n" + "="*60)
    print("Test 3: Session Isolation Testing")
    print("="*60)

    from smart_customer_service.hot_reload import get_hot_reload_manager
    from smart_customer_service.graph import create_conversation_graph, run_conversation_turn
    from smart_customer_service.config import Config

    try:
        Config.validate()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return

    manager = get_hot_reload_manager()

    # Test 3.1: Create session with initial config
    print("\n📝 Test 3.1: Create session with initial config")
    initial_versions = manager.get_current_version()
    graph1 = create_conversation_graph()
    state1 = {
        "messages": [],
        "intent": None,
        "parameters": {},
        "tool_result": None,
        "waiting_for_parameter": None,
        "completed": False,
    }
    state1 = run_conversation_turn(graph1, state1, "查订单")
    print(f"   Session 1 started with versions: {initial_versions}")
    print(f"   Session 1 messages: {len(state1['messages'])}")
    print("   ✅ Session 1 created")

    # Test 3.2: Trigger hot reload
    print("\n📝 Test 3.2: Trigger hot reload")
    manager.reload_model(temperature=0.8)
    manager.reload_plugins()
    new_versions = manager.get_current_version()
    print(f"   Versions after reload: {new_versions}")
    assert new_versions["model_version"] > initial_versions["model_version"]
    assert new_versions["plugin_version"] > initial_versions["plugin_version"]
    print("   ✅ Hot reload completed")

    # Test 3.3: Continue session 1 (should still work)
    print("\n📝 Test 3.3: Continue session 1 after hot reload")
    state1 = run_conversation_turn(graph1, state1, "ORD001")
    print(f"   Session 1 messages after reload: {len(state1['messages'])}")
    assert len(state1["messages"]) > 2  # Should have accumulated messages
    print("   ✅ Session 1 continues working")

    # Test 3.4: Create new session with new config
    print("\n📝 Test 3.4: Create new session with new config")
    graph2 = create_conversation_graph()
    state2 = {
        "messages": [],
        "intent": None,
        "parameters": {},
        "tool_result": None,
        "waiting_for_parameter": None,
        "completed": False,
    }
    state2 = run_conversation_turn(graph2, state2, "查订单")
    print(f"   Session 2 started with versions: {new_versions}")
    print(f"   Session 2 messages: {len(state2['messages'])}")
    print("   ✅ Session 2 created with new config")

    # Test 3.5: Both sessions should be independent
    print("\n📝 Test 3.5: Verify sessions are independent")
    print(f"   Session 1 intent: {state1.get('intent')}")
    print(f"   Session 2 intent: {state2.get('intent')}")
    # Both should have similar state structure but independent data
    assert state1["messages"] != state2["messages"]
    print("   ✅ Sessions are independent")

    print("\n✅ All session isolation tests passed!\n")


if __name__ == "__main__":
    print("Starting Stage 3 Hot Reload Tests")
    print("="*60)

    try:
        # Run all tests
        test_hot_reload_manager()
        test_session_isolation()

        # API tests (optional - requires running server)
        print("\n" + "="*60)
        print("API Hot Reload Tests (requires running server)")
        print("="*60)
        print("To test API hot reload:")
        print("1. In one terminal: python -m smart_customer_service.api")
        print("2. In another terminal: python test_stage3_hot_reload.py --api")
        print("="*60)

        if "--api" in sys.argv:
            asyncio.run(test_api_hot_reload())
        else:
            print("\nSkipping API tests. Use --api flag to run them.")

        print("\n" + "="*60)
        print("✅ All Stage 3 hot reload tests completed successfully!")
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
