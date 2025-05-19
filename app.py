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
    st.session_state.user_profile = None
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
if "last_tool_html" not in st.session_state:
    st.session_state.last_tool_html = ""
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
            for msg in history:
                if msg["role"] in ["user", "assistant"]:
                    st.session_state.messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
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
    st.session_state.messages.append({"role": "user", "content": user_input})
    context.add_message("user", user_input)
    with st.chat_message("user"):
        st.markdown(user_input)

    # 助手消息容器
    assistant_container = st.chat_message("assistant")
    with assistant_container:
        st.markdown("*正在处理...*")
        tools_placeholder = st.empty()
        message_placeholder = st.empty()
        
        # 清除之前可能显示的工具调用内容
        if st.session_state.show_tools:
            tools_placeholder.empty()

    # 工具调用追踪
    final_tool_html = ""
    tool_done = False
    def tool_update_callback(html_report):
        nonlocal final_tool_html, tool_done
        final_tool_html = html_report
        st.session_state.last_tool_html = html_report
        if st.session_state.show_tools:
            html_content = f"""
            <div style='margin-bottom: 20px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.08); background-color: #FFFFFF; border: 1px solid rgba(0,0,0,0.05);'>
                <div style='padding: 12px 16px; background-color: #F5F9FF; border-bottom: 1px solid rgba(0,0,0,0.05); display: flex; align-items: center;'>
                    <span style='margin-right: 8px; font-size: 18px;'>🔧</span>
                    <h4 style='margin: 0; color: #424242; font-size: 1em; font-weight: 600;'>工具调用过程</h4>
                </div>
                <div style='padding: 8px;'>
                    <div id='tool-calls' style='overflow-y: auto;'>{html_report}</div>
                </div>
            </div>
            """
            render_html(tools_placeholder, html_content)
        tool_done = True
    st.session_state.tool_tracker.clear()
    st.session_state.tool_tracker.set_update_callback(tool_update_callback)

    # 用户偏好分析
    preferences = preference_tool.extract_preferences(user_input)
    st.session_state.user_profile.update_profile(preferences)

    # --- 工具意图检测与调用 ---
    tool_traces = tool_registry.detect_and_run(user_input)
    script_content = None
    for trace in tool_traces:
        if trace["status"] == "success" and trace["result"]:
            script_content = trace["result"]
            break
    # 工具trace结构化展示
    if st.session_state.show_tools and tool_traces:
        html = f"""
        <div style='margin-bottom: 20px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.08); background-color: #FFFFFF; border: 1px solid rgba(0,0,0,0.05);'>
            <div style='padding: 12px 16px; background-color: #F5F9FF; border-bottom: 1px solid rgba(0,0,0,0.05); display: flex; align-items: center;'>
                <span style='margin-right: 8px; font-size: 18px;'>🔧</span>
                <h4 style='margin: 0; color: #424242; font-size: 1em; font-weight: 600;'>工具调用过程</h4>
            </div>
            <div style='padding: 8px;'>
        """
        
        for trace in tool_traces:
            # 根据状态决定卡片风格
            if trace['status'] == 'success':
                card_bg = "#F9FBF9"
                status_color = "#2E7D32"
                status_icon = "&#10004;"  # 勾
            else:
                card_bg = "#FEF8F8"
                status_color = "#D32F2F"
                status_icon = "&#10060;"  # 错
                
            html += f"""
                <div style='margin-bottom: 12px; border-radius: 6px; overflow: hidden; border: 1px solid rgba(0,0,0,0.05); background-color: {card_bg};'>
                    <div style='padding: 10px 12px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(0,0,0,0.03);'>
                        <span style='font-weight: 600; color: #424242; font-size: 0.95em;'>{trace['intent']}</span>
                        <div style='display: flex; align-items: center;'>
                            <span style='color: {status_color}; font-weight: 500; font-size: 1em; margin-right: 4px;'>{status_icon}</span>
                            <span style='color: {status_color}; font-size: 0.85em;'>{trace['status'].capitalize()}</span>
                        </div>
                    </div>
                    <div style='padding: 12px;'>
                        <div style='margin-bottom: 8px;'>
                            <div style='font-weight: 500; color: #616161; font-size: 0.85em; margin-bottom: 4px;'>{trace['description']}</div>
                        </div>
                        <div style='margin-bottom: 8px;'>
                            <div style='font-weight: 500; color: #616161; font-size: 0.8em; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px;'>参数</div>
                            <div style='font-family: monospace; white-space: pre-wrap; font-size: 0.85em; line-height: 1.4; color: #424242; background-color: rgba(0,0,0,0.03); padding: 8px; border-radius: 4px;'>{trace['params']}</div>
                        </div>
            """
            
            if trace['status'] == 'success':
                output_str = str(trace['result'])
                # 创建一个唯一ID用于展开/收起长内容
                result_id = f"result_{int(time.time() * 1000)}_{trace['intent']}"
                
                if len(output_str) > 300:
                    html += f"""
                        <div>
                            <div style='font-weight: 500; color: #616161; font-size: 0.8em; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; display: flex; justify-content: space-between;'>
                                <span>结果</span>
                                <button onclick="toggleResult('{result_id}')" style="background: none; border: none; color: #1E88E5; cursor: pointer; font-size: 0.85em; padding: 2px 6px;">展开完整内容</button>
                            </div>
                            <div id="{result_id}_preview" style='font-family: monospace; white-space: pre-wrap; font-size: 0.85em; line-height: 1.4; color: #424242; background-color: rgba(46,125,50,0.05); padding: 8px; border-radius: 4px; display: block;'>{output_str[:300]}...</div>
                            <div id="{result_id}_full" style='font-family: monospace; white-space: pre-wrap; font-size: 0.85em; line-height: 1.4; color: #424242; background-color: rgba(46,125,50,0.05); padding: 8px; border-radius: 4px; max-height: 800px; overflow-y: auto; display: none;'>{output_str}</div>
                        </div>
                    """
                else:
                    html += f"""
                        <div>
                            <div style='font-weight: 500; color: #616161; font-size: 0.8em; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px;'>结果</div>
                            <div style='font-family: monospace; white-space: pre-wrap; font-size: 0.85em; line-height: 1.4; color: #424242; background-color: rgba(46,125,50,0.05); padding: 8px; border-radius: 4px;'>{output_str}</div>
                        </div>
                    """
            else:
                html += f"""
                        <div>
                            <div style='font-weight: 500; color: #616161; font-size: 0.8em; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px;'>错误</div>
                            <div style='font-family: monospace; white-space: pre-wrap; font-size: 0.85em; line-height: 1.4; color: #D32F2F; background-color: rgba(211,47,47,0.05); padding: 8px; border-radius: 4px;'>{trace['error']}</div>
                        </div>
                """
                
            html += """
                    </div>
                </div>
            """
            
        # 添加长内容展开/收起的JavaScript函数
        html += """
            </div>
        </div>
        <script>
        function toggleResult(resultId) {
            const preview = document.getElementById(resultId + '_preview');
            const full = document.getElementById(resultId + '_full');
            const button = document.querySelector(`button[onclick="toggleResult('${resultId}')"]`);
            
            if (preview.style.display === 'none') {
                preview.style.display = 'block';
                full.style.display = 'none';
                button.textContent = '展开完整内容';
            } else {
                preview.style.display = 'none';
                full.style.display = 'block';
                button.textContent = '收起';
            }
        }
        </script>
        """
        render_html(tools_placeholder, html)
        time.sleep(0.3)
        render_html(message_placeholder, "<p><em>工具调用已完成，正在生成回复...</em></p>")
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
            
            # 只在必要时更新工具调用区域，避免频繁重新渲染
            if st.session_state.show_tools and final_tool_html and tool_done:
                # 使用静态变量跟踪是否已渲染工具调用
                if not hasattr(stream_callback, "tool_html_rendered"):
                    stream_callback.tool_html_rendered = True
                    html_content = f"""
                    <div style='margin-bottom: 20px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.08); background-color: #FFFFFF; border: 1px solid rgba(0,0,0,0.05);'>
                        <div style='padding: 12px 16px; background-color: #F5F9FF; border-bottom: 1px solid rgba(0,0,0,0.05); display: flex; align-items: center;'>
                            <span style='margin-right: 8px; font-size: 18px;'>🔧</span>
                            <h4 style='margin: 0; color: #424242; font-size: 1em; font-weight: 600;'>工具调用过程</h4>
                        </div>
                        <div style='padding: 16px;'>
                            <div id='tool-calls' style='overflow-y: auto;'>{final_tool_html}</div>
                        </div>
                    </div>
                    """
                    render_html(tools_placeholder, html_content)
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
        # 确保最终回复完整显示
        st.session_state.messages[-1]["content"] = full_response
        time.sleep(0.3)
        render_html(message_placeholder, f"{full_response}")
        context.add_message("assistant", full_response)
        
        # 确保工具调用区域显示完整，但避免重复渲染
        if st.session_state.show_tools and final_tool_html and not hasattr(stream_callback, "tool_html_rendered"):
            html_content = f"""
            <div style='margin-bottom: 20px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.08); background-color: #FFFFFF; border: 1px solid rgba(0,0,0,0.05);'>
                <div style='padding: 12px 16px; background-color: #F5F9FF; border-bottom: 1px solid rgba(0,0,0,0.05); display: flex; align-items: center;'>
                    <span style='margin-right: 8px; font-size: 18px;'>🔧</span>
                    <h4 style='margin: 0; color: #424242; font-size: 1em; font-weight: 600;'>工具调用过程</h4>
                </div>
                <div style='padding: 16px;'>
                    <div id='tool-calls' style='overflow-y: auto;'>{final_tool_html}</div>
                </div>
            </div>
            """
            render_html(tools_placeholder, html_content)
        st.session_state.output_complete = True
        st.session_state.is_generating = False
    except Exception as e:
        st.error(f"生成回复时出错: {e}")
        if full_response:
            st.session_state.messages[-1]["content"] = full_response
            render_html(message_placeholder, f"{full_response}")
            context.add_message("assistant", full_response)
        else:
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant" and not st.session_state.messages[-1]["content"]:
                st.session_state.messages.pop()
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
    message_index = 0
    # 显示所有历史消息
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.markdown(message["content"])
        else:
            with st.chat_message("assistant"):
                # 如果是最后一条助手消息并且有保存的工具调用HTML，显示工具调用
                is_last_message = message == st.session_state.messages[-1]
                should_show_tools = (
                    is_last_message and 
                    "last_tool_html" in st.session_state and 
                    st.session_state.last_tool_html and 
                    st.session_state.show_tools and 
                    st.session_state.output_complete and
                    not st.session_state.is_generating  # 如果正在生成新消息，不显示历史工具调用
                )
                
                if should_show_tools:
                    tools_placeholder = st.empty()
                    html_content = f"""
                    <div style='margin-bottom: 20px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.08); background-color: #FFFFFF; border: 1px solid rgba(0,0,0,0.05);'>
                        <div style='padding: 12px 16px; background-color: #F5F9FF; border-bottom: 1px solid rgba(0,0,0,0.05); display: flex; align-items: center;'>
                            <span style='margin-right: 8px; font-size: 18px;'>🔧</span>
                            <h4 style='margin: 0; color: #424242; font-size: 1em; font-weight: 600;'>工具调用过程</h4>
                        </div>
                        <div style='padding: 16px;'>
                            <div id='tool-calls' style='overflow-y: auto;'>{st.session_state.last_tool_html}</div>
                        </div>
                    </div>
                    """
                    render_html(tools_placeholder, html_content)
                
                # 显示助手回复
                st.markdown(message["content"])
        message_index += 1
    
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