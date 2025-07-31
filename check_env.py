#!/usr/bin/env python3
"""
环境检查脚本
"""
import sys
import os
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    print(f"Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version >= (3, 10):
        print("✓ Python版本符合要求 (>=3.10)")
        return True
    else:
        print("✗ Python版本过低，需要3.10+")
        return False

def check_required_packages():
    """检查必需的包"""
    required_packages = [
        ('dotenv', 'python-dotenv'),
        ('pandas', 'pandas'),
        ('pathlib', '内置模块'),
        ('json', '内置模块'),
        ('asyncio', '内置模块')
    ]
    
    missing_packages = []
    
    for package_name, install_name in required_packages:
        try:
            __import__(package_name)
            print(f"✓ {package_name} 可用")
        except ImportError:
            print(f"✗ {package_name} 缺失 (安装: {install_name})")
            if install_name != '内置模块':
                missing_packages.append(install_name)
    
    return missing_packages

def check_optional_packages():
    """检查可选包"""
    optional_packages = [
        ('docx', 'python-docx'),
        ('llama_index', 'llama-index'),
        ('streamlit', 'streamlit'),
        ('chromadb', 'chromadb')
    ]
    
    available_count = 0
    
    for package_name, install_name in optional_packages:
        try:
            __import__(package_name)
            print(f"✓ {package_name} 可用")
            available_count += 1
        except ImportError:
            print(f"- {package_name} 不可用 (可安装: {install_name})")
    
    print(f"可选包可用性: {available_count}/{len(optional_packages)}")
    return available_count

def check_directories():
    """检查目录结构"""
    base_dir = Path(__file__).parent
    required_dirs = [
        "src",
        "data",
        "data/knowledge_base",
        "data/chroma_db",
        "data/student_data"
    ]
    
    all_exist = True
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if dir_path.exists():
            print(f"✓ {dir_name} 存在")
        else:
            print(f"✗ {dir_name} 不存在")
            all_exist = False
    
    return all_exist

def check_config():
    """检查配置文件"""
    base_dir = Path(__file__).parent
    
    # 检查.env.example
    env_example = base_dir / ".env.example"
    if env_example.exists():
        print("✓ .env.example 存在")
    else:
        print("✗ .env.example 不存在")
    
    # 检查.env
    env_file = base_dir / ".env"
    if env_file.exists():
        print("✓ .env 存在")
        return True
    else:
        print("- .env 不存在 (可从.env.example复制)")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("环境检查")
    print("=" * 50)
    
    print("\n1. Python版本检查:")
    python_ok = check_python_version()
    
    print("\n2. 必需包检查:")
    missing_packages = check_required_packages()
    
    print("\n3. 可选包检查:")
    available_optional = check_optional_packages()
    
    print("\n4. 目录结构检查:")
    dirs_ok = check_directories()
    
    print("\n5. 配置文件检查:")
    config_ok = check_config()
    
    print("\n" + "=" * 50)
    print("检查结果:")
    
    if python_ok and not missing_packages and dirs_ok:
        print("✓ 基础环境正常")
        if available_optional >= 2:
            print("✓ 系统可以运行基础功能")
            if config_ok:
                print("✓ 配置文件就绪")
                print("\n推荐操作:")
                print("1. 编辑 .env 文件，配置 OpenAI API Key")
                print("2. 运行: python main.py")
            else:
                print("\n推荐操作:")
                print("1. 复制 .env.example 为 .env")
                print("2. 编辑 .env 文件，配置必要参数")
        else:
            print("! 部分可选功能不可用")
            print(f"\n缺少依赖包:")
            for pkg in missing_packages:
                print(f"  - {pkg}")
            print("\n安装建议:")
            print("运行: uv sync  # 安装所有依赖")
    else:
        print("✗ 环境存在问题")
        if missing_packages:
            print(f"缺少必需包: {', '.join(missing_packages)}")
        if not dirs_ok:
            print("目录结构不完整")
    
    print("\n当前可运行的功能:")
    if not missing_packages:
        print("- 配置检查")
        print("- 基础数据处理")
    if available_optional >= 1:
        print("- 部分模块功能")
    if available_optional >= 3:
        print("- 完整系统功能")

if __name__ == "__main__":
    main()