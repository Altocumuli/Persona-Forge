"""
PersonaForge 演示脚本

PersonaForge 是一个支持人设定制、流式输出、用户画像分析和专业工具集成的大语言模型交互平台。演示模式适合新用户快速体验人设对话、剧本工具等主要功能。
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

# 加载环境变量
load_dotenv()

from config.config import PERSONAS_DIR
from src.model.persona import PersonaManager
from src.model.llm_config import LLMManager
from src.utils.context_manager import SessionManager
from src.tools.preference_tool import PreferenceTool, UserProfile
from src.tools.script_tool import ScriptTool


def demo_conversation():
    """演示简单对话"""
    # 设置API密钥
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("错误: 未设置DashScope API密钥。请设置DASHSCOPE_API_KEY环境变量。")
        return
    
    # 初始化组件
    print("正在初始化组件...")
    persona_manager = PersonaManager(PERSONAS_DIR)
    llm_manager = LLMManager(api_key=api_key)
    session_manager = SessionManager()
    
    # 创建会话
    session_id = "demo_session"
    context = session_manager.create_session(session_id)
    
    # 创建用户画像
    user_profile = UserProfile(session_id)
    
    # 创建工具
    preference_tool = PreferenceTool(llm=llm_manager.create_llm({"temperature": 0.1}))
    
    # 加载人设
    available_personas = persona_manager.list_personas()
    if not available_personas:
        print("错误: 没有可用的人设。请先创建人设配置。")
        return
    
    persona_name = available_personas[0]  # 使用第一个可用人设
    persona = persona_manager.get_persona(persona_name)
    print(f"已加载人设: {persona.name} ({persona.role})")
    
    # 预设对话
    conversations = [
        "你好，请介绍一下你自己。",
        "我想写一个关于时间旅行的故事，有什么建议？",
        "主角应该是什么样的人？",
        "谢谢你的建议，再见！",
    ]
    
    # 进行对话
    print("\n" + "="*50)
    print("开始演示对话:")
    print("="*50 + "\n")
    
    for user_input in conversations:
        print(f"用户: {user_input}")
        
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
        
        print("-"*50)


def demo_script_tool():
    """演示剧本工具"""
    # 设置API密钥
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("错误: 未设置DashScope API密钥。请设置DASHSCOPE_API_KEY环境变量。")
        return
    
    # 初始化组件
    print("正在初始化组件...")
    llm_manager = LLMManager(api_key=api_key)
    
    # 创建剧本工具
    script_tool = ScriptTool(llm=llm_manager.create_llm({"temperature": 0.7}))
    
    # 演示剧本规划
    print("\n" + "="*50)
    print("剧本规划演示:")
    print("="*50 + "\n")
    
    context = {
        "genre": "科幻剧情",
        "theme": "时间旅行与人性",
        "characters": ["艾玛 - 物理学家", "马克 - 时间旅行者", "莉莉 - 艾玛的女儿"],
        "setting": "2050年的科技城市",
        "duration": "2小时"
    }
    
    print("请求剧本规划，内容如下:")
    for key, value in context.items():
        if isinstance(value, list):
            print(f"{key}: {', '.join(value)}")
        else:
            print(f"{key}: {value}")
    
    print("\n规划结果:")
    result = script_tool.create_script_plan(context)
    print(result)
    
    # 演示角色档案生成
    print("\n" + "="*50)
    print("角色档案生成演示:")
    print("="*50 + "\n")
    
    character_info = {
        "name": "马克",
        "age": "35岁",
        "background": "前军人，意外获得时间旅行能力",
        "personality": "坚毅、固执、有责任感",
        "goals": "找到改变过去的方法，拯救在战争中失去的家人"
    }
    
    print("请求角色档案生成，角色信息如下:")
    for key, value in character_info.items():
        print(f"{key}: {value}")
    
    print("\n角色档案:")
    result = script_tool.generate_character_profile(character_info)
    print(result)


if __name__ == "__main__":
    print("PersonaForge 演示")
    print("-------------------\n")
    
    while True:
        print("\n请选择演示类型:")
        print("1. 对话演示")
        print("2. 剧本工具演示")
        print("0. 退出")
        
        choice = input("\n请输入选项编号: ")
        
        if choice == "1":
            demo_conversation()
        elif choice == "2":
            demo_script_tool()
        elif choice == "0":
            print("演示结束，再见！")
            break
        else:
            print("无效的选项，请重试。") 