"""
剧本相关工具，用于辅助剧本创作和规划
"""
from typing import Dict, Any, List, Optional
import json
from langchain_core.tools import Tool
from langchain_community.llms.tongyi import Tongyi
from src.utils.prompt_builder import PromptBuilder


class ScriptTool:
    """剧本工具，提供剧本创作和规划相关功能"""
    
    def __init__(self, llm: Optional[Tongyi] = None, tracker=None):
        """初始化剧本工具
        
        Args:
            llm: 语言模型实例，如果为None则创建一个新实例
            tracker: 工具跟踪器实例
        """
        if llm is None:
            from config.config import DEFAULT_LLM_CONFIG, DASHSCOPE_API_KEY, DASHSCOPE_API_BASE
            self.llm = Tongyi(
                model_name=DEFAULT_LLM_CONFIG.get("model_name", "qwen-turbo"),
                dashscope_api_key=DASHSCOPE_API_KEY,
                model_kwargs={"temperature": 0.7},  # 使用较高的温度以增加创意性
                endpoint_url=DASHSCOPE_API_BASE
            )
        else:
            self.llm = llm
        
        self.tracker = tracker
    
    def create_script_plan(self, context: Dict[str, Any]) -> str:
        """创建剧本规划
        
        Args:
            context: 剧本上下文信息，包含类型、主题、角色等
            
        Returns:
            剧本规划
        """
        # 如果有跟踪器，记录工具调用开始
        if self.tracker:
            self.tracker.start_trace("创建剧本规划", context)
        
        try:
            genre = context.get("genre", "未知类型")
            theme = context.get("theme", "未知主题")
            characters = context.get("characters", [])
            setting = context.get("setting", "未知设定")
            duration = context.get("duration", "未知时长")
            
            # 格式化角色列表
            characters_str = "、".join(characters) if characters else "未指定角色"
            
            prompt = f"""
    请为以下剧本创建一个详细的故事大纲和结构规划：

    类型: {genre}
    主题: {theme}
    角色: {characters_str}
    设定: {setting}
    时长: {duration}

    请提供以下内容：
    1. 故事概述 (一段简短的故事摘要)
    2. 主要角色介绍和发展轨迹
    3. 分为三幕的结构规划:
        - 第一幕: 设置和介绍
        - 第二幕: 冲突和发展
        - 第三幕: 高潮和解决
    4. 关键场景列表和简要描述
    5. 主要情感线索和主题元素
    """
            
            # 调用模型获取结果
            response = self.llm.invoke(prompt)
            
            # 如果有跟踪器，记录工具调用完成
            if self.tracker:
                # # 截断结果如果太长
                # result_summary = response[:200] + "..." if len(response) > 200 else response
                result_summary = response
                self.tracker.complete_trace(result_summary)
            
            return response
        except Exception as e:
            # 如果有跟踪器，记录工具调用失败
            if self.tracker:
                self.tracker.fail_trace(str(e))
            
            # 返回错误信息
            return f"创建剧本规划时出错: {e}"
    
    def generate_character_profile(self, character_info: Dict[str, Any]) -> str:
        """生成角色档案
        
        Args:
            character_info: 角色信息
            
        Returns:
            角色档案
        """
        # 如果有跟踪器，记录工具调用开始
        if self.tracker:
            self.tracker.start_trace("生成角色档案", character_info)
        
        try:
            name = character_info.get("name", "未命名角色")
            age = character_info.get("age", "未知")
            background = character_info.get("background", "未知")
            personality = character_info.get("personality", "未知")
            goals = character_info.get("goals", "未知")
            
            prompt = f"""
    创建一个详细的角色档案，基于以下信息：

    姓名: {name}
    年龄: {age}
    背景: {background}
    性格特点: {personality}
    目标/动机: {goals}

    请提供以下内容：
    1. 详细的角色背景故事
    2. 人物性格分析
    3. 外表和行为描述
    4. 与其他角色的关系可能性
    5. 角色发展潜力和转折点建议
    """
            
            # 调用模型获取结果
            response = self.llm.invoke(prompt)
            
            # 如果有跟踪器，记录工具调用完成
            if self.tracker:
                # # 截断结果如果太长
                # result_summary = response[:200] + "..." if len(response) > 200 else response
                result_summary = response
                self.tracker.complete_trace(result_summary)
            
            return response
        except Exception as e:
            # 如果有跟踪器，记录工具调用失败
            if self.tracker:
                self.tracker.fail_trace(str(e))
            
            # 返回错误信息
            return f"生成角色档案时出错: {e}"
    
    def generate_dialogue(self, dialogue_context: Dict[str, Any]) -> str:
        """生成对话
        
        Args:
            dialogue_context: 对话上下文信息
            
        Returns:
            生成的对话
        """
        # 如果有跟踪器，记录工具调用开始
        if self.tracker:
            self.tracker.start_trace("生成对话", dialogue_context)
        
        try:
            characters = dialogue_context.get("characters", [])
            scene = dialogue_context.get("scene", "未知场景")
            situation = dialogue_context.get("situation", "未知情境")
            tone = dialogue_context.get("tone", "自然")
            length = dialogue_context.get("length", "中等")
            
            # 格式化角色列表
            characters_str = "、".join(characters) if characters else "未指定角色"
            
            prompt = f"""
    请为以下场景创建一段对话：

    角色: {characters_str}
    场景: {scene}
    情境: {situation}
    语气/风格: {tone}
    长度: {length}

    请创建自然流畅、符合角色特性的对话。对话应包含角色之间的交流、冲突或合作，并推动情节发展。
    """
            
            # 调用模型获取结果
            response = self.llm.invoke(prompt)
            
            # 如果有跟踪器，记录工具调用完成
            if self.tracker:
                # # 截断结果如果太长
                # result_summary = response[:200] + "..." if len(response) > 200 else response
                result_summary = response
                self.tracker.complete_trace(result_summary)
            
            return response
        except Exception as e:
            # 如果有跟踪器，记录工具调用失败
            if self.tracker:
                self.tracker.fail_trace(str(e))
            
            # 返回错误信息
            return f"生成对话时出错: {e}"
    
    def analyze_script(self, script_content: str) -> Dict[str, Any]:
        """分析剧本内容
        
        Args:
            script_content: 剧本内容
            
        Returns:
            分析结果
        """
        prompt = f"""
分析以下剧本内容，并提供详细评估。输出应为JSON格式，包含以下字段：
- structure: 对剧本结构的分析
- characters: 对角色塑造的分析
- dialogue: 对对话质量的分析
- pacing: 对节奏的分析
- themes: 识别的主题
- strengths: 剧本的优点
- weaknesses: 需要改进的地方
- suggestions: 改进建议

剧本内容:
{script_content}
"""
        
        # 调用模型获取结果
        response = self.llm.invoke(prompt)
        
        # 解析JSON结果
        try:
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            # 如果解析失败，返回基本结构
            return {
                "structure": "无法分析",
                "characters": "无法分析",
                "dialogue": "无法分析",
                "pacing": "无法分析",
                "themes": [],
                "strengths": [],
                "weaknesses": [],
                "suggestions": []
            }
    
    def get_planning_tool(self) -> Tool:
        """获取剧本规划工具
        
        Returns:
            LangChain工具实例
        """
        return Tool(
            name="script_planning_tool",
            description="为给定的剧本需求创建详细的规划方案",
            func=self.create_script_plan
        )
    
    def get_character_tool(self) -> Tool:
        """获取角色生成工具
        
        Returns:
            LangChain工具实例
        """
        return Tool(
            name="character_profile_tool",
            description="为给定的角色信息生成详细的角色档案",
            func=self.generate_character_profile
        )
    
    def get_dialogue_tool(self) -> Tool:
        """获取对话生成工具
        
        Returns:
            LangChain工具实例
        """
        return Tool(
            name="dialogue_generation_tool",
            description="为给定的场景和角色生成对话",
            func=self.generate_dialogue
        )
    
    def get_analysis_tool(self) -> Tool:
        """获取剧本分析工具
        
        Returns:
            LangChain工具实例
        """
        return Tool(
            name="script_analysis_tool",
            description="分析给定的剧本内容并提供详细评估",
            func=self.analyze_script
        ) 