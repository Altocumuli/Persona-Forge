"""
用户偏好获取工具
"""
from typing import Dict, Any, List, Optional
import json
from langchain_core.tools import Tool
from langchain_community.llms.tongyi import Tongyi
from src.utils.prompt_builder import PromptBuilder


class PreferenceTool:
    """用户偏好分析工具"""
    
    def __init__(self, llm: Optional[Tongyi] = None, tracker=None):
        """初始化用户偏好工具
        
        Args:
            llm: 语言模型实例，如果为None则创建一个新实例
            tracker: 工具跟踪器实例
        """
        if llm is None:
            from config.config import DEFAULT_LLM_CONFIG, DASHSCOPE_API_KEY, DASHSCOPE_API_BASE
            self.llm = Tongyi(
                model_name=DEFAULT_LLM_CONFIG.get("model_name", "qwen-turbo"),
                dashscope_api_key=DASHSCOPE_API_KEY,
                model_kwargs={"temperature": 0.1},  # 低温度，确保输出更确定性
                endpoint_url=DASHSCOPE_API_BASE
            )
        else:
            self.llm = llm
        
        self.tracker = tracker
    
    def extract_preferences(self, user_input: str) -> Dict[str, Any]:
        """从用户输入中提取偏好
        
        Args:
            user_input: 用户输入
            
        Returns:
            提取的偏好数据
        """
        # 如果有跟踪器，记录工具调用开始
        if self.tracker:
            self.tracker.start_trace("提取用户偏好", {"user_input": user_input})
        
        try:
            # 构建提取偏好的提示词
            prompt = PromptBuilder.build_preference_extraction_prompt(user_input)
            
            # 调用模型获取结果
            response = self.llm.invoke(prompt)
            
            # 尝试清理和修正LLM返回的结果
            cleaned_response = response.strip()
            # 移除可能的前缀文本，比如"```json"或"以下是结果："
            if "```json" in cleaned_response:
                cleaned_response = cleaned_response.split("```json", 1)[1]
            if "```" in cleaned_response:
                cleaned_response = cleaned_response.split("```", 1)[1]
                if "```" in cleaned_response:
                    cleaned_response = cleaned_response.rsplit("```", 1)[0]
            
            # 查找JSON开始的位置
            json_start = cleaned_response.find('{')
            if json_start >= 0:
                cleaned_response = cleaned_response[json_start:]
                
                # 查找JSON结束的位置
                json_end = cleaned_response.rfind('}')
                if json_end >= 0:
                    cleaned_response = cleaned_response[:json_end+1]
            
            # 解析JSON结果
            try:
                result = json.loads(cleaned_response)
                
                # 确保结果包含所有必要的字段
                if "topics" not in result:
                    result["topics"] = []
                if "preferences" not in result:
                    result["preferences"] = {}
                if "goals" not in result:
                    result["goals"] = []
                if "concerns" not in result:
                    result["concerns"] = []
                if "context" not in result:
                    result["context"] = {}
                
                # 如果有跟踪器，记录工具调用完成
                if self.tracker:
                    self.tracker.complete_trace(result)
                
                return result
            except json.JSONDecodeError as json_err:
                # 如果解析失败，返回基本结构
                default_result = {
                    "topics": [],
                    "preferences": {},
                    "goals": [],
                    "concerns": [],
                    "context": {}
                }
                
                # 如果有跟踪器，记录工具调用失败
                if self.tracker:
                    self.tracker.fail_trace(f"JSON解析失败: {str(json_err)}\n原始响应: {response[:100]}...")
                
                return default_result
        except Exception as e:
            # 如果有跟踪器，记录工具调用失败
            if self.tracker:
                self.tracker.fail_trace(f"工具执行失败: {str(e)}")
            
            # 返回空结果
            return {
                "topics": [],
                "preferences": {},
                "goals": [],
                "concerns": [],
                "context": {}
            }
    
    def get_langchain_tool(self) -> Tool:
        """获取LangChain工具
        
        Returns:
            LangChain工具实例
        """
        return Tool(
            name="user_preference_tool",
            description="从用户输入中提取用户偏好、兴趣和需求",
            func=self.extract_preferences
        )


class UserProfile:
    """用户画像管理"""
    
    def __init__(self, user_id: str):
        """初始化用户画像
        
        Args:
            user_id: 用户ID
        """
        self.user_id = user_id
        self.preferences: Dict[str, Any] = {
            "topics": [],        # 感兴趣的主题
            "preferences": {},   # 各类偏好
            "goals": [],         # 目标或需求
            "concerns": [],      # 担忧或顾虑
            "context": {}        # 上下文信息
        }
        self.interaction_count = 0
        
    def update_profile(self, new_preferences: Dict[str, Any]) -> None:
        """更新用户画像
        
        Args:
            new_preferences: 新的偏好数据
        """
        # 更新主题
        if "topics" in new_preferences and new_preferences["topics"]:
            for topic in new_preferences["topics"]:
                if topic not in self.preferences["topics"]:
                    self.preferences["topics"].append(topic)
        
        # 更新偏好
        if "preferences" in new_preferences and new_preferences["preferences"]:
            self.preferences["preferences"].update(new_preferences["preferences"])
        
        # 更新目标
        if "goals" in new_preferences and new_preferences["goals"]:
            for goal in new_preferences["goals"]:
                if goal not in self.preferences["goals"]:
                    self.preferences["goals"].append(goal)
        
        # 更新担忧
        if "concerns" in new_preferences and new_preferences["concerns"]:
            for concern in new_preferences["concerns"]:
                if concern not in self.preferences["concerns"]:
                    self.preferences["concerns"].append(concern)
        
        # 更新上下文
        if "context" in new_preferences and new_preferences["context"]:
            self.preferences["context"].update(new_preferences["context"])
        
        # 更新交互计数
        self.interaction_count += 1
    
    def get_profile(self) -> Dict[str, Any]:
        """获取用户画像
        
        Returns:
            用户画像数据
        """
        return {
            "user_id": self.user_id,
            "preferences": self.preferences,
            "interaction_count": self.interaction_count
        }
    
    def get_topics_as_text(self) -> str:
        """获取主题文本描述
        
        Returns:
            主题描述文本
        """
        if not self.preferences["topics"]:
            return "未知"
        
        return "、".join(self.preferences["topics"])
    
    def get_goals_as_text(self) -> str:
        """获取目标文本描述
        
        Returns:
            目标描述文本
        """
        if not self.preferences["goals"]:
            return "未知"
        
        return "、".join(self.preferences["goals"])
    
    def get_persona_enhancement(self) -> str:
        """获取人设增强提示词
        
        Returns:
            增强提示词
        """
        topics = self.get_topics_as_text()
        goals = self.get_goals_as_text()
        
        return f"""
用户画像信息：
- 感兴趣的主题: {topics}
- 目标或需求: {goals}
- 交互次数: {self.interaction_count}

请根据以上用户画像信息，调整你的回答，使其更符合用户的需求和偏好。
""" 