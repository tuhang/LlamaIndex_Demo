#!/usr/bin/env python3
"""
Quick system test
"""
import sys
import os
from pathlib import Path

def main():
    print("=" * 50)
    print("Education RAG System - Quick Test")
    print("=" * 50)
    
    # Check Python version
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    # Check basic modules
    basic_modules = ['json', 'pathlib', 'asyncio', 'datetime']
    print("\nBasic modules:")
    for module in basic_modules:
        try:
            __import__(module)
            print(f"  OK: {module}")
        except ImportError:
            print(f"  FAIL: {module}")
    
    # Check directories
    base_dir = Path(__file__).parent
    dirs = ['src', 'data', 'data/knowledge_base', 'data/chroma_db']
    print("\nDirectories:")
    for d in dirs:
        path = base_dir / d
        if path.exists():
            print(f"  OK: {d}")
        else:
            print(f"  MISSING: {d}")
    
    # Check files
    files = ['config.py', 'main.py', '.env.example']
    print("\nCore files:")
    for f in files:
        path = base_dir / f
        if path.exists():
            print(f"  OK: {f}")
        else:
            print(f"  MISSING: {f}")
    
    # Try to import config
    print("\nConfig test:")
    try:
        sys.path.insert(0, str(base_dir))
        from config import settings
        print(f"  OK: Config loaded")
        print(f"  Knowledge base dir: {settings.knowledge_base_dir}")
        print(f"  OpenAI API Key: {'Configured' if settings.openai_api_key else 'Not configured'}")
    except Exception as e:
        print(f"  FAIL: Config import failed: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("\nNext steps:")
    print("1. Install dependencies: uv sync")
    print("2. Copy .env.example to .env and configure")
    print("3. Run: python main.py")

if __name__ == "__main__":
    main()