"""
PersonaForge 启动脚本

PersonaForge 是一个支持人设定制、流式输出、用户画像分析和专业工具集成的大语言模型交互平台。该启动脚本可一键切换命令行、Web界面和演示三种模式，满足不同用户需求。
"""
import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 检查API密钥
api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    print("警告: 未设置DASHSCOPE_API_KEY环境变量。")
    print("请在运行前设置环境变量或创建.env文件。")
    print("示例: DASHSCOPE_API_KEY=sk-xxxxx")
    print("\n请选择操作:")
    print("1. 输入API密钥并继续")
    print("2. 退出")
    
    choice = input("\n请输入选项编号: ")
    if choice == "1":
        api_key = input("请输入DashScope API密钥: ").strip()
        os.environ["DASHSCOPE_API_KEY"] = api_key
    else:
        sys.exit(0)

# 获取当前目录
current_dir = Path(__file__).parent

# 检查依赖
try:
    import streamlit
    import langchain
except ImportError:
    print("正在安装依赖...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(current_dir / "requirements.txt")])

# 显示菜单
while True:
    print("\n" + "="*50)
    print("PersonaForge 智能对话平台")
    print("="*50)
    print("请选择启动模式:")
    print("1. 命令行模式")
    print("2. Web界面模式")
    print("3. 演示模式")
    print("0. 退出")
    
    choice = input("\n请输入选项编号: ")
    
    if choice == "1":
        # 命令行模式
        subprocess.call([sys.executable, str(current_dir / "main.py")])
    elif choice == "2":
        # Web界面模式
        print("正在启动Web界面...")
        print("请稍等片刻，浏览器窗口将自动打开。")
        subprocess.call(["streamlit", "run", str(current_dir / "app.py")])
    elif choice == "3":
        # 演示模式
        subprocess.call([sys.executable, str(current_dir / "examples/demo.py")])
    elif choice == "0":
        print("再见！")
        break
    else:
        print("无效的选项，请重试。") 