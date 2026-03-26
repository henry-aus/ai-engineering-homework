"""Main entry point for the smart customer service chatbot."""
import json
from pathlib import Path
from datetime import datetime

from .chain import extract_info
from .config import Config


def setup_logging():
    """Create logs directory if it doesn't exist."""
    log_dir = Path(Config.LOG_DIR)
    log_dir.mkdir(exist_ok=True)
    return log_dir


def log_extraction(extracted_info, log_dir: Path):
    """Log extracted information to console and file."""

    # Print to console with formatting
    print("\n" + "="*60)
    print("📊 提取的结构化信息:")
    print("="*60)
    print(json.dumps(
        extracted_info.model_dump(),
        ensure_ascii=False,
        indent=2
    ))
    print("="*60 + "\n")

    # Append to log file
    log_file = log_dir / "queries.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            **extracted_info.model_dump()
        }
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


def generate_response(extracted_info) -> str:
    """Generate a friendly response based on extracted information."""

    intent_map = {
        "order_query": "查询订单",
        "refund_request": "申请退款",
        "invoice_request": "开具发票",
        "general": "咨询"
    }

    intent_text = intent_map.get(extracted_info.intent, "咨询")

    if extracted_info.date_mentioned and extracted_info.original_date_expression:
        return f"好的，我看到您想{intent_text}，时间是 {extracted_info.date_mentioned} ({extracted_info.original_date_expression})。[已记录查询意图]"
    elif extracted_info.date_mentioned:
        return f"好的，我看到您想{intent_text}，时间是 {extracted_info.date_mentioned}。[已记录查询意图]"
    else:
        return f"好的，我看到您想{intent_text}。[已记录查询意图]"


def main():
    """Main CLI chat loop."""

    print("="*60)
    print("🤖 智能客服系统 - Stage 1")
    print("="*60)
    print("💡 功能：基础对话 + 时间推断")
    print("💬 输入 '退出'、'exit' 或 'quit' 结束对话")
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
    print(f"📝 日志文件: {log_dir / 'queries.jsonl'}\n")

    # Chat loop
    try:
        while True:
            # Get user input
            user_input = input("👤 您: ").strip()

            # Check for exit commands
            if user_input.lower() in ["退出", "exit", "quit", "q"]:
                print("\n👋 再见！感谢使用智能客服系统。")
                break

            # Skip empty input
            if not user_input:
                continue

            # Extract information
            print("🔍 正在分析...")
            extracted_info = extract_info(user_input)

            # Log extraction
            log_extraction(extracted_info, log_dir)

            # Generate and display response
            response = generate_response(extracted_info)
            print(f"🤖 客服: {response}\n")

    except KeyboardInterrupt:
        print("\n\n👋 再见！感谢使用智能客服系统。")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        raise


if __name__ == "__main__":
    main()
