"""Verification script to check if setup is correct."""

import sys


def verify_imports():
    """Verify all required packages can be imported."""
    print("Checking imports...")
    errors = []

    try:
        import langchain
        print(f"  ✓ langchain {langchain.__version__}")
    except ImportError as e:
        errors.append(f"  ✗ langchain: {e}")

    try:
        import langgraph
        print(f"  ✓ langgraph (imported successfully)")
    except ImportError as e:
        errors.append(f"  ✗ langgraph: {e}")

    try:
        import faiss
        print(f"  ✓ faiss (imported successfully)")
    except ImportError as e:
        errors.append(f"  ✗ faiss: {e}")

    try:
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
        print(f"  ✓ langchain_openai")
    except ImportError as e:
        errors.append(f"  ✗ langchain_openai: {e}")

    try:
        from rich.console import Console
        print(f"  ✓ rich")
    except ImportError as e:
        errors.append(f"  ✗ rich: {e}")

    try:
        import structlog
        print(f"  ✓ structlog")
    except ImportError as e:
        errors.append(f"  ✗ structlog: {e}")

    return errors


def verify_modules():
    """Verify werewolf modules can be imported."""
    print("\nChecking werewolf modules...")
    errors = []

    modules = [
        "werewolf.game.state",
        "werewolf.game.graph",
        "werewolf.game.phases",
        "werewolf.agents.player",
        "werewolf.memory.semantic",
        "werewolf.prompts.system_prompts",
        "werewolf.prompts.personalities",
        "werewolf.tracing.tracker",
        "werewolf.utils.llm",
        "werewolf.utils.logging",
    ]

    for module in modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except Exception as e:
            errors.append(f"  ✗ {module}: {e}")

    return errors


def verify_env():
    """Verify environment configuration."""
    print("\nChecking environment...")
    import os
    from pathlib import Path

    errors = []

    # Check .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("  ⚠ .env file not found (copy from .env.example)")
        errors.append("  Missing .env file")
    else:
        print("  ✓ .env file exists")

    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("  ⚠ OPENAI_API_KEY not set in environment")
        errors.append("  Missing OPENAI_API_KEY")
    elif api_key == "your_api_key_here":
        print("  ⚠ OPENAI_API_KEY needs to be updated in .env")
        errors.append("  Default OPENAI_API_KEY value")
    else:
        print(f"  ✓ OPENAI_API_KEY set ({api_key[:8]}...)")

    return errors


def main():
    """Run all verification checks."""
    print("="*60)
    print("Werewolf Game Setup Verification")
    print("="*60)

    all_errors = []

    # Run checks
    all_errors.extend(verify_imports())
    all_errors.extend(verify_modules())
    all_errors.extend(verify_env())

    # Summary
    print("\n" + "="*60)
    if not all_errors:
        print("✓ All checks passed! Setup is complete.")
        print("\nTo run the game:")
        print("  python -m werewolf.main")
        return 0
    else:
        print(f"✗ Found {len(all_errors)} issue(s):")
        for error in all_errors:
            print(error)
        print("\nPlease fix these issues before running the game.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
