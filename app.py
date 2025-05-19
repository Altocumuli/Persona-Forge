"""
PersonaForge Web界面

PersonaForge 是一个支持人设定制、流式输出、用户画像分析和专业工具集成的大语言模型交互平台。Web界面模式适合所有用户，提供直观的图形化操作、丰富的会话与工具体验。
"""
import os
import time
import uuid
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from config.config import PERSONAS_DIR
from src.model.persona import PersonaManager, PersonaConfig
from src.model.llm_config import LLMManager
from src.utils.context_manager import SessionManager
from src.tools.preference_tool import PreferenceTool, UserProfile
from src.tools.script_tool import ScriptTool
from src.utils.tool_tracker import ToolTracker
from src.tools.tool_registry import ToolIntent, ToolIntentRegistry
from src.tools.param_extractor_tool import ParamExtractor


# 初始化会话状态
if "session_id" not in st.session_state:
    st.session_state.session_id = f"session_{uuid.uuid4().hex[:8]}"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_profile" not in st.session_state:
    st.session_state.user_profile = UserProfile(st.session_state.session_id)
if "persona" not in st.session_state:
    st.session_state.persona = None
if "history_loaded" not in st.session_state:
    st.session_state.history_loaded = False
if "is_generating" not in st.session_state:
    st.session_state.is_generating = False
if "tool_tracker" not in st.session_state:
    st.session_state.tool_tracker = ToolTracker()
if "show_tools" not in st.session_state:
    st.session_state.show_tools = True
if "current_turn_tool_html" not in st.session_state:
    st.session_state.current_turn_tool_html = ""
if "output_complete" not in st.session_state:
    st.session_state.output_complete = True


def initialize_components():
    """初始化系统组件"""
    # 设置API密钥
    api_key = os.getenv("DASHSCOPE_API_KEY")
    api_base = os.getenv("DASHSCOPE_API_BASE")
    
    if not api_key:
        st.error("错误: 未设置DashScope API密钥。请在.env文件中设置DASHSCOPE_API_KEY环境变量。")
        st.stop()
    
    # 初始化组件
    persona_manager = PersonaManager(PERSONAS_DIR)
    llm_manager = LLMManager(api_key=api_key, api_base=api_base)
    session_manager = SessionManager()
    
    # 获取或创建会话
    context = session_manager.get_session(st.session_state.session_id)
    if not context:
        context = session_manager.create_session(st.session_state.session_id)
    
    # 创建用户画像
    if st.session_state.user_profile is None:
        st.session_state.user_profile = UserProfile(st.session_state.session_id)
    
    # 获取或创建工具跟踪器
    tool_tracker = st.session_state.tool_tracker
    
    # 创建工具
    preference_tool = PreferenceTool(
        llm=llm_manager.create_llm({"temperature": 0.1}),
        tracker=tool_tracker
    )
    script_tool = ScriptTool(
        llm=llm_manager.create_llm({"temperature": 0.7}),
        tracker=tool_tracker
    )
    
    # 加载消息历史
    if not st.session_state.history_loaded:
        history = context.get_history()
        if history:
            processed_history = []
            for i, msg in enumerate(history):
                # Adapt old history format to new format with IDs and tool_html
                # Assuming old history might not have tool_html or specific IDs
                processed_history.append({
                    "id": f"history_{st.session_state.session_id}_{i}", # Generate a stable ID
                    "role": msg["role"],
                    "content": msg["content"],
                    "tool_html": msg.get("tool_html") # Preserve if already exists, else None
                })
            st.session_state.messages = processed_history
        else:
            st.session_state.messages = [] # Ensure it's initialized if no history
        st.session_state.history_loaded = True
    
    return persona_manager, llm_manager, session_manager, context, preference_tool, script_tool


def load_persona(persona_name: str, persona_manager: PersonaManager) -> PersonaConfig:
    """加载人设
    
    Args:
        persona_name: 人设名称
        persona_manager: 人设管理器
        
    Returns:
        人设配置
    """
    persona = persona_manager.get_persona(persona_name)
    if persona:
        st.session_state.persona = persona
    return persona


def create_persona_panel(persona_manager: PersonaManager):
    """创建人设面板
    
    Args:
        persona_manager: 人设管理器
    """
    with st.sidebar:
        st.title("PersonaForge")
        
        # 会话信息
        st.subheader("会话信息")
        st.text(f"会话ID: {st.session_state.session_id}")
        if st.button("创建新会话"):
            st.session_state.session_id = f"session_{uuid.uuid4().hex[:8]}"
            st.session_state.messages = []
            st.session_state.history_loaded = False
            st.session_state.user_profile = None
            st.rerun()
        
        st.divider()
        
        # 人设选择
        st.subheader("人设选择")
        available_personas = persona_manager.list_personas()
        
        if not available_personas:
            st.warning("没有可用的人设。请先创建人设配置。")
        else:
            current_persona = None
            if st.session_state.persona:
                current_persona = st.session_state.persona.name
            
            persona_name = st.selectbox(
                "选择人设",
                available_personas,
                index=available_personas.index(current_persona) if current_persona in available_personas else 0
            )
            
            if st.button("加载人设"):
                persona = load_persona(persona_name, persona_manager)
                if persona:
                    st.success(f"已加载人设: {persona.name}")
                    st.rerun()
        
        st.divider()
        
        # 显示当前人设
        if st.session_state.persona:
            persona = st.session_state.persona
            st.subheader("当前人设")
            st.text(f"名称: {persona.name}")
            st.text(f"角色: {persona.role}")
            
            with st.expander("人设详情"):
                st.subheader("描述")
                st.text(persona.description)
                
                st.subheader("行为准则")
                st.text(persona.guidelines)
                
                st.subheader("风格")
                st.text(persona.style)
        
        st.divider()
        
        # 系统设置
        st.subheader("系统设置")
        show_tools = st.checkbox("显示工具调用过程", value=st.session_state.show_tools)
        if show_tools != st.session_state.show_tools:
            st.session_state.show_tools = show_tools
            st.rerun()

        st.subheader("关于PersonaForge")
        st.write("""
PersonaForge 允许用户为大语言模型设定特定的角色、风格和行为模式，实现个性化、可视化的智能对话体验。

系统特点:
- 多样化的角色定制与切换
- 个性化的交互与用户画像
- 持久化的对话历史与会话管理
- 工具调用可视化与剧本创作辅助

开始使用:
1. 在侧边栏选择一个预设人设
2. 点击"加载人设"按钮
3. 开始与PersonaForge对话
""")

# 初始化LLM和参数提取器
if "param_extractor" not in st.session_state:
    param_llm = LLMManager(api_key=os.getenv("DASHSCOPE_API_KEY"), api_base=os.getenv("DASHSCOPE_API_BASE")).create_llm({"temperature": 0.1})
    st.session_state.param_extractor = ParamExtractor(param_llm)
else:
    param_llm = None
    param_extractor = st.session_state.param_extractor

# 工具注册表初始化（只需初始化一次）
if "tool_registry" not in st.session_state:
    tool_registry = ToolIntentRegistry()
    param_extractor = st.session_state.param_extractor
    # 注册剧本大纲工具
    tool_registry.register(ToolIntent(
        name="script_plan",
        keywords=["剧本", "故事", "电影", "规划", "大纲"],
        param_extractor=param_extractor.extract_script_plan_params,
        tool_func=lambda params: ScriptTool(
            llm=LLMManager(api_key=os.getenv("DASHSCOPE_API_KEY"), api_base=os.getenv("DASHSCOPE_API_BASE")).create_llm({"temperature": 0.7}),
            tracker=st.session_state.tool_tracker
        ).create_script_plan(params),
        description="生成剧本大纲"
    ))
    # 注册角色档案工具
    tool_registry.register(ToolIntent(
        name="character_profile",
        keywords=["角色", "人物", "档案", "资料"],
        param_extractor=param_extractor.extract_character_profile_params,
        tool_func=lambda params: ScriptTool(
            llm=LLMManager(api_key=os.getenv("DASHSCOPE_API_KEY"), api_base=os.getenv("DASHSCOPE_API_BASE")).create_llm({"temperature": 0.7}),
            tracker=st.session_state.tool_tracker
        ).generate_character_profile(params),
        description="生成角色档案"
    ))
    # 注册对话生成工具
    tool_registry.register(ToolIntent(
        name="dialogue",
        keywords=["对话", "台词", "对白"],
        param_extractor=param_extractor.extract_dialogue_params,
        tool_func=lambda params: ScriptTool(
            llm=LLMManager(api_key=os.getenv("DASHSCOPE_API_KEY"), api_base=os.getenv("DASHSCOPE_API_BASE")).create_llm({"temperature": 0.7}),
            tracker=st.session_state.tool_tracker
        ).generate_dialogue(params),
        description="生成对话"
    ))
    
    # 导入编程工具和关键词配置
    from src.tools.code_analyzer_tool import CodeAnalyzerTool
    from src.tools.tool_registry import CODE_ANALYZE_KEYWORDS, CODE_IMPROVE_KEYWORDS, CODE_DIAGNOSIS_KEYWORDS, LEARNING_PLAN_KEYWORDS
    
    # 注册代码分析工具
    tool_registry.register(ToolIntent(
        name="code_analyzer",
        keywords=CODE_ANALYZE_KEYWORDS,
        param_extractor=param_extractor.extract_code_analysis_params,
        tool_func=lambda params: CodeAnalyzerTool(
            llm=LLMManager(api_key=os.getenv("DASHSCOPE_API_KEY"), api_base=os.getenv("DASHSCOPE_API_BASE")).create_llm({"temperature": 0.5}),
            tracker=st.session_state.tool_tracker
        ).analyze_code(params),
        description="分析代码结构和质量"
    ))
    
    # 注册代码优化建议工具
    tool_registry.register(ToolIntent(
        name="code_improver",
        keywords=CODE_IMPROVE_KEYWORDS,
        param_extractor=param_extractor.extract_code_improvement_params,
        tool_func=lambda params: CodeAnalyzerTool(
            llm=LLMManager(api_key=os.getenv("DASHSCOPE_API_KEY"), api_base=os.getenv("DASHSCOPE_API_BASE")).create_llm({"temperature": 0.5}),
            tracker=st.session_state.tool_tracker
        ).suggest_code_improvements(params),
        description="为代码提供优化和改进建议"
    ))
    
    # 注册代码问题诊断工具
    tool_registry.register(ToolIntent(
        name="code_diagnostics",
        keywords=CODE_DIAGNOSIS_KEYWORDS,
        param_extractor=param_extractor.extract_code_diagnosis_params,
        tool_func=lambda params: CodeAnalyzerTool(
            llm=LLMManager(api_key=os.getenv("DASHSCOPE_API_KEY"), api_base=os.getenv("DASHSCOPE_API_BASE")).create_llm({"temperature": 0.5}),
            tracker=st.session_state.tool_tracker
        ).diagnose_code_issue(params),
        description="诊断代码错误和问题"
    ))
    
    # 注册学习计划生成工具
    tool_registry.register(ToolIntent(
        name="learning_plan_generator",
        keywords=LEARNING_PLAN_KEYWORDS,
        param_extractor=param_extractor.extract_learning_plan_params,
        tool_func=lambda params: CodeAnalyzerTool(
            llm=LLMManager(api_key=os.getenv("DASHSCOPE_API_KEY"), api_base=os.getenv("DASHSCOPE_API_BASE")).create_llm({"temperature": 0.6}),
            tracker=st.session_state.tool_tracker
        ).generate_learning_plan(params),
        description="生成个性化的编程学习计划"
    ))
    
    st.session_state.tool_registry = tool_registry
else:
    tool_registry = st.session_state.tool_registry


def handle_message(
    user_input: str,
    context,
    llm_manager: LLMManager,
    preference_tool: PreferenceTool,
    script_tool: ScriptTool
):
    """处理用户消息（重构版）"""
    if not st.session_state.persona:
        st.error("请先选择一个人设")
        return

    st.session_state.output_complete = False
    st.session_state.is_generating = True

    # 添加用户消息
    user_msg_id = f"user_{uuid.uuid4().hex[:8]}"
    st.session_state.messages.append({
        "id": user_msg_id,
        "role": "user",
        "content": user_input,
        "tool_html": None
    })
    context.add_message("user", user_input)
    with st.chat_message("user"):
        st.markdown(user_input)

    # 助手消息容器 和 占位符
    assistant_msg_id = f"assistant_{uuid.uuid4().hex[:8]}"
    st.session_state.messages.append({
        "id": assistant_msg_id,
        "role": "assistant",
        "content": "", # Placeholder for content
        "tool_html": None # Placeholder for tool html
    })
    current_assistant_message_index = len(st.session_state.messages) - 1

    assistant_container = st.chat_message("assistant")
    with assistant_container:
        st.markdown("*正在处理...*") # Initial text in assistant message bubble
        tools_placeholder = st.empty()  # Placeholder for tool display
        message_placeholder = st.empty() # Placeholder for LLM response and status messages
        
        message_placeholder.markdown("*正在分析您的请求...*") # Initial status

    # Tool callback updates current_turn_tool_html AND renders to tools_placeholder
    def tool_update_callback(html_report):
        st.session_state.current_turn_tool_html = html_report
        if st.session_state.show_tools:
            if html_report and html_report.strip() != "<div>没有工具调用记录</div>":
                # Wrap the report from ToolTracker with the standard header
                styled_html_report = (
                    f"<div style='margin-bottom: 20px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.08); background-color: #FFFFFF; border: 1px solid rgba(0,0,0,0.05);'>"
                    f"    <div style='padding: 12px 16px; background-color: #F5F9FF; border-bottom: 1px solid rgba(0,0,0,0.05); display: flex; align-items: center;'>"
                    f"        <span style='margin-right: 8px; font-size: 18px;'>🔧</span>"
                    f"        <h4 style='margin: 0; color: #424242; font-size: 1em; font-weight: 600;'>工具调用过程</h4>"
                    f"    </div>"
                    f"    <div style='padding: 8px;'>"
                    f"        {html_report}"
                    f"    </div>"
                    f"</div>"
                )
                render_html(tools_placeholder, styled_html_report)
            else:
                tools_placeholder.empty() # Clear if no tools or report is empty

    st.session_state.tool_tracker.clear() # This will call tool_update_callback, clearing the tools_placeholder
    st.session_state.tool_tracker.set_update_callback(tool_update_callback)

    # 用户偏好分析
    preferences = preference_tool.extract_preferences(user_input)
    st.session_state.user_profile.update_profile(preferences)

    # --- 工具意图检测与调用 ---
    # detect_and_run will trigger tool_update_callback for each tool event
    tool_traces_summary = tool_registry.detect_and_run(user_input) 
    
    script_content = None
    # Extract script_content from the summary if needed
    for trace_summary in tool_traces_summary:
        if trace_summary["status"] == "success" and trace_summary["result"]:
            script_content = trace_summary["result"]
            break
    
    # --- Explicitly render the final tool state before moving to LLM response --- 
    if st.session_state.show_tools:
        final_html_report = st.session_state.current_turn_tool_html
        if final_html_report and final_html_report.strip() != "<div>没有工具调用记录</div>":
            styled_final_html_report = (
                f"<div style='margin-bottom: 20px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.08); background-color: #FFFFFF; border: 1px solid rgba(0,0,0,0.05);'>"
                f"    <div style='padding: 12px 16px; background-color: #F5F9FF; border-bottom: 1px solid rgba(0,0,0,0.05); display: flex; align-items: center;'>"
                f"        <span style='margin-right: 8px; font-size: 18px;'>🔧</span>"
                f"        <h4 style='margin: 0; color: #424242; font-size: 1em; font-weight: 600;'>工具调用过程</h4>"
                f"    </div>"
                f"    <div style='padding: 8px;'>"  # User's change from 16px to 8px
                f"        {final_html_report}"
                f"    </div>"
                f"</div>"
            )
            render_html(tools_placeholder, styled_final_html_report)
        else:
            tools_placeholder.empty() # Ensure it's clear if no tools were actually run or logged
    
    # --- Update message placeholder after tool execution phase ---
    if st.session_state.show_tools and st.session_state.current_turn_tool_html and st.session_state.current_turn_tool_html.strip() != "<div>没有工具调用记录</div>":
        render_html(message_placeholder, "<p><em>工具调用已完成，正在生成回复...</em></p>")
    else:
        # Tools were not shown, or no tools were called/logged.
        render_html(message_placeholder, "<p><em>正在生成回复...</em></p>")
    # A brief pause for the user to see the status update before LLM generation starts erasing it.
    # This might be overwritten quickly by the stream_callback, so its impact might be minimal.
    # Consider if this time.sleep is beneficial or if the stream_callback's first write is sufficient.
    time.sleep(0.2) 

    # --- 构建系统提示词 ---
    persona = st.session_state.persona
    persona_enhancement = st.session_state.user_profile.get_persona_enhancement()
    enhanced_prompt = persona.get_system_prompt() + "\n\n" + persona_enhancement
    if script_content:
        script_context = f"""
用户请求与剧本相关的内容，我已经生成了以下内容:

{script_content}

在回复中，请基于上述生成的内容回应用户的请求。你可以以自然、友好的语言介绍这些内容，并可以添加你的观点或建议。
"""
        enhanced_prompt += "\n\n" + script_context

    # --- 生成模型回复 ---
    st.session_state.messages.append({"role": "assistant", "content": ""})
    full_response = ""
    def stream_callback(chunk):
        nonlocal full_response
        if chunk:
            full_response += chunk
            st.session_state.messages[-1]["content"] = full_response
            render_html(message_placeholder, f"{full_response}▌")
            
            # Tool HTML is rendered before streaming starts, no need to update here.
            time.sleep(0.01)
    try:
        history = context.get_history()
        llm_manager.generate_response(
            persona=persona,
            user_input=user_input,
            conversation_history=history[:-1],
            streaming_callback=stream_callback,
            system_prompt=enhanced_prompt
        )
        # Ensure final full response is in the message object (stream_callback does this)
        # Now, save the tool HTML for this completed assistant message
        if st.session_state.current_turn_tool_html and st.session_state.current_turn_tool_html.strip() != "<div>没有工具调用记录</div>":
            st.session_state.messages[current_assistant_message_index]["tool_html"] = st.session_state.current_turn_tool_html
        else:
            st.session_state.messages[current_assistant_message_index]["tool_html"] = None # Ensure it's None if no tools were run

        # Clear current turn tool HTML as it has been committed or was not used
        st.session_state.current_turn_tool_html = ""
        
        # Final render of the completed message content (already done by stream_callback's last call)
        # render_html(message_placeholder, f"{full_response}") 
        context.add_message("assistant", full_response)
        
        st.session_state.output_complete = True
        st.session_state.is_generating = False
    except Exception as e:
        st.error(f"生成回复时出错: {e}")
        if full_response: # If some response was generated before error
            st.session_state.messages[current_assistant_message_index]["content"] = full_response
            # Potentially save partial tool HTML if relevant, or leave as None
            if st.session_state.current_turn_tool_html and st.session_state.current_turn_tool_html.strip() != "<div>没有工具调用记录</div>":
                 st.session_state.messages[current_assistant_message_index]["tool_html"] = st.session_state.current_turn_tool_html
            context.add_message("assistant", full_response) # Save partial response to context
        else: # If no response at all, and placeholder was added
            if st.session_state.messages and st.session_state.messages[-1]["id"] == assistant_msg_id: # Check if the last msg is our placeholder
                st.session_state.messages.pop() # Remove the empty assistant message placeholder
        
        st.session_state.current_turn_tool_html = "" # Clear on error too
        st.session_state.is_generating = False
        st.session_state.output_complete = True


def create_chat_interface(
    context,
    llm_manager: LLMManager,
    preference_tool: PreferenceTool,
    script_tool: ScriptTool
):
    """创建聊天界面
    
    Args:
        context: 上下文管理器
        llm_manager: LLM管理器
        preference_tool: 偏好工具
        script_tool: 剧本工具
    """
    # 显示所有历史消息
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            # Display tool HTML for assistant messages if available and enabled
            if message["role"] == "assistant" and message.get("tool_html") and st.session_state.show_tools:
                tool_html_content = message["tool_html"]
                # Wrap the stored tool_html with the standard header and styling
                styled_tool_html = (
                    f"<div style='margin-bottom: 20px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.08); background-color: #FFFFFF; border: 1px solid rgba(0,0,0,0.05);'>"
                    f"    <div style='padding: 12px 16px; background-color: #F5F9FF; border-bottom: 1px solid rgba(0,0,0,0.05); display: flex; align-items: center;'>"
                    f"        <span style='margin-right: 8px; font-size: 18px;'>🔧</span>"
                    f"        <h4 style='margin: 0; color: #424242; font-size: 1em; font-weight: 600;'>工具调用过程</h4>"
                    f"    </div>"
                    f"    <div style='padding: 8px;'>" # Consistent padding
                    f"        {tool_html_content}"
                    f"    </div>"
                    f"</div>"
                )
                st.markdown(styled_tool_html, unsafe_allow_html=True)
            
            # Display message content
            st.markdown(message["content"])
    
    # 聊天输入
    if user_input := st.chat_input("输入您的消息...", disabled=st.session_state.is_generating):
        handle_message(user_input, context, llm_manager, preference_tool, script_tool)


def main():
    """主程序入口"""
    st.set_page_config(
        page_title="PersonaForge",
        page_icon="🤖",
        layout="wide",
    )
    
    # 添加自定义CSS样式
    st.markdown("""
    <style>
    .assistant-message {
        padding: 10px;
        border-radius: 10px;
        background-color: #f0f2f6;
        font-size: 16px;
        line-height: 1.5;
        animation: fadeIn 0.3s ease-in-out;
    }
    @keyframes fadeIn {
        from { opacity: 0.7; }
        to { opacity: 1; }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 初始化组件
    persona_manager, llm_manager, session_manager, context, preference_tool, script_tool = initialize_components()
    
    # 创建人设面板
    create_persona_panel(persona_manager)
    
    # 创建聊天界面
    if st.session_state.persona:
        create_chat_interface(context, llm_manager, preference_tool, script_tool)
    else:
        st.info("请在侧边栏选择一个人设开始对话。")
        
        st.subheader("关于PersonaForge")
        st.write("""
PersonaForge 允许用户为大语言模型设定特定的角色、风格和行为模式，实现个性化、可视化的智能对话体验。

系统特点:
- 多样化的角色定制与切换
- 个性化的交互与用户画像
- 持久化的对话历史与会话管理
- 工具调用可视化与剧本创作辅助

开始使用:
1. 在侧边栏选择一个预设人设
2. 点击"加载人设"按钮
3. 开始与PersonaForge对话
""")


# 实用函数：安全渲染HTML内容
def render_html(placeholder, html_content):
    """使用markdown安全渲染HTML内容
    
    Args:
        placeholder: Streamlit占位符
        html_content: HTML内容
    """
    placeholder.markdown(html_content, unsafe_allow_html=True)


if __name__ == "__main__":
    main() 