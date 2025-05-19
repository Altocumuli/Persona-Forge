"""
PersonaForge 命令行模式入口

PersonaForge 是一个支持人设定制、流式输出、用户画像分析和专业工具集成的大语言模型交互平台。命令行模式适合开发者和进阶用户，支持高效对话、角色切换和工具调用。
"""
import os
import argparse
import uuid
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from config.config import PERSONAS_DIR
from src.model.persona import PersonaManager
from src.model.llm_config import LLMManager
from src.utils.context_manager import SessionManager
from src.tools.preference_tool import PreferenceTool, UserProfile
from src.tools.script_tool import ScriptTool


def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description="PersonaForge 命令行模式 - 支持人设定制、流式输出、用户画像和专业工具")
    parser.add_argument("--persona", "-p", type=str, help="指定使用的人设")
    parser.add_argument("--api-key", type=str, help="DashScope API密钥")
    parser.add_argument("--api-base", type=str, help="DashScope API基础URL")
    parser.add_argument("--session", "-s", type=str, help="会话ID")
    parser.add_argument("--non-interactive", action="store_true", help="非交互模式")
    
    args = parser.parse_args()
    
    # 设置API密钥
    api_key = args.api_key or os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("错误: 未提供DashScope API密钥。请使用--api-key参数或设置DASHSCOPE_API_KEY环境变量。")
        return
    
    # 创建会话ID
    session_id = args.session or f"session_{uuid.uuid4().hex[:8]}"
    
    # 初始化组件
    persona_manager = PersonaManager(PERSONAS_DIR)
    llm_manager = LLMManager(api_key=api_key, api_base=args.api_base)
    session_manager = SessionManager()
    
    # 获取或创建会话
    context = session_manager.get_session(session_id)
    if not context:
        context = session_manager.create_session(session_id)
        print(f"创建新会话: {session_id}")
    else:
        print(f"加载现有会话: {session_id}")
    
    # 创建用户画像
    user_profile = UserProfile(session_id)
    
    # 创建工具
    preference_tool = PreferenceTool(llm=llm_manager.create_llm({"temperature": 0.1}))
    script_tool = ScriptTool(llm=llm_manager.create_llm({"temperature": 0.7}))
    
    # 加载人设
    if args.persona:
        persona = persona_manager.get_persona(args.persona)
        if not persona:
            print(f"错误: 找不到指定的人设 '{args.persona}'")
            available_personas = persona_manager.list_personas()
            if available_personas:
                print(f"可用人设: {', '.join(available_personas)}")
            return
    else:
        # 列出可用人设
        available_personas = persona_manager.list_personas()
        if not available_personas:
            print("错误: 没有可用的人设。请先创建人设配置。")
            return
        
        print("可用人设:")
        for i, persona_name in enumerate(available_personas):
            print(f"{i+1}. {persona_name}")
        
        # 选择人设
        while True:
            try:
                choice = int(input("\n请选择人设 (输入编号): "))
                if 1 <= choice <= len(available_personas):
                    persona = persona_manager.get_persona(available_personas[choice-1])
                    break
                else:
                    print("无效的选择，请重试。")
            except ValueError:
                print("请输入有效的数字。")
    
    print(f"\n已加载人设: {persona.name} ({persona.role})")
    print("\n" + "="*50)
    print("欢迎使用 PersonaForge 命令行模式！")
    print("输入 'exit' 或 'quit' 退出对话")
    print("输入 'clear' 清空对话历史")
    print("="*50 + "\n")
    
    # 交互循环
    while True:
        # 获取用户输入
        user_input = input("用户: ")
        
        # 处理特殊命令
        if user_input.lower() in ["exit", "quit"]:
            print("再见！")
            break
        elif user_input.lower() == "clear":
            context.clear_history()
            print("已清空对话历史。")
            continue
        
        # 添加用户消息到历史
        context.add_message("user", user_input)
        
        # 分析用户偏好并更新用户画像
        preferences = preference_tool.extract_preferences(user_input)
        user_profile.update_profile(preferences)
        
        # 获取对话历史
        history = context.get_history()
        
        # 获取用户画像增强提示
        persona_enhancement = user_profile.get_persona_enhancement()
        
        # 增强系统提示词
        enhanced_prompt = persona.get_system_prompt() + "\n\n" + persona_enhancement
        
        # 生成回复
        try:
            # 定义流式输出回调函数
            response_text = ""
            def stream_callback(chunk):
                nonlocal response_text
                response_text += chunk
                # 实时打印（不换行）
                print(chunk, end="", flush=True)
            
            # 先打印角色名称
            print(f"\n{persona.role}: ", end="", flush=True)
            
            # 生成回复（使用流式输出）
            response = llm_manager.generate_response(
                persona=persona,
                user_input=user_input,
                conversation_history=history[:-1],  # 排除刚刚添加的用户消息
                system_prompt=enhanced_prompt,  # 使用增强后的系统提示词
                streaming_callback=stream_callback
            )
            
            # 完成后打印换行
            print("\n")
            
            # 添加助手消息到历史
            context.add_message("assistant", response_text)
        except Exception as e:
            print(f"生成回复时出错: {e}")
    
    # 保存会话
    print(f"会话已保存: {session_id}")


if __name__ == "__main__":
    main() 