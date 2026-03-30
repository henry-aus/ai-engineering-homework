"""Main entry point for the smart customer service chatbot."""
import json
from pathlib import Path
from datetime import datetime

from .config import Config
from .graph import create_conversation_graph, run_conversation_turn


def setup_logging():
    """Create logs directory if it doesn't exist."""
    log_dir = Path(Config.LOG_DIR)
    log_dir.mkdir(exist_ok=True)
    return log_dir


def log_conversation_turn(state, log_dir: Path):
    """Log conversation state to file."""
    log_file = log_dir / "conversations.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "intent": state.get("intent"),
            "parameters": state.get("parameters", {}),
            "tool_result": state.get("tool_result"),
            "message_count": len(state.get("messages", [])),
        }
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


def main():
    """Main CLI chat loop with multi-turn conversation support."""

    print("="*60)
    print("🤖 智能客服系统 - Stage 2")
    print("="*60)
    print("💡 功能：多轮对话 + 工具调用")
    print("🔧 支持：订单查询、退款申请、发票开具")
    print("💬 输入 '退出'、'exit' 或 'quit' 结束对话")
    print("💬 输入 'reset' 重置对话状态")
    print("="*60 + "\n")

    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        print(f"❌ 配置错误: {e}")
        print("💡 请在项目根目录创建 .env 文件，并设置 OPENAI_API_KEY")
        return

    # Setup logging
    log_dir = setup_logging()
    print(f"📝 日志文件: {log_dir / 'conversations.jsonl'}\n")

    # Create conversation graph
    try:
        graph = create_conversation_graph()
        print("✅ 对话系统已初始化\n")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return

    # Initialize conversation state
    state = {
        "messages": [],
        "intent": None,
        "parameters": {},
        "tool_result": None,
        "waiting_for_parameter": None,
        "completed": False,
    }

    # Chat loop
    try:
        while True:
            # Get user input
            user_input = input("👤 您: ").strip()

            # Check for exit commands
            if user_input.lower() in ["退出", "exit", "quit", "q"]:
                print("\n👋 再见！感谢使用智能客服系统。")
                break

            # Check for reset command
            if user_input.lower() == "reset":
                state = {
                    "messages": [],
                    "intent": None,
                    "parameters": {},
                    "tool_result": None,
                    "waiting_for_parameter": None,
                    "completed": False,
                }
                print("🔄 对话状态已重置\n")
                continue

            # Skip empty input
            if not user_input:
                continue

            # Run conversation turn
            print("🔍 正在处理...")
            state = run_conversation_turn(graph, state, user_input)

            # Log the turn
            log_conversation_turn(state, log_dir)

            # Display assistant's response
            messages = state.get("messages", [])
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, 'content') and last_message.type == "ai":
                    print(f"🤖 客服: {last_message.content}\n")

    except KeyboardInterrupt:
        print("\n\n👋 再见！感谢使用智能客服系统。")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
