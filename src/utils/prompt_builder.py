"""
提示词构建工具，用于构建各种场景下的提示词
"""
from typing import List, Dict, Any, Optional
from src.model.persona import PersonaConfig


class PromptBuilder:
    """提示词构建器，用于构建各种场景下的提示词"""
    
    @staticmethod
    def build_system_prompt(persona: PersonaConfig) -> str:
        """构建系统提示词
        
        Args:
            persona: 人设配置
            
        Returns:
            系统提示词
        """
        return persona.get_system_prompt()
    
    @staticmethod
    def build_few_shot_examples(persona: PersonaConfig) -> List[Dict[str, str]]:
        """构建few-shot示例
        
        Args:
            persona: 人设配置
            
        Returns:
            示例消息列表
        """
        if not persona.examples:
            return []
        
        examples = []
        for example in persona.examples:
            examples.append({"role": "user", "content": example.user})
            examples.append({"role": "assistant", "content": example.assistant})
        
        return examples
    
    @staticmethod
    def build_preference_extraction_prompt(user_input: str) -> str:
        """构建用户偏好提取提示词
        
        Args:
            user_input: 用户输入
            
        Returns:
            提示词
        """
        # 定义示例JSON响应
        example_json = '''
{
  "topics": ["剧本创作", "电影"],
  "preferences": {"类型": "喜剧", "风格": "轻松"},
  "goals": ["获得创意灵感", "写出好剧本"],
  "concerns": ["质量不高", "不够有趣"],
  "context": {"当前活动": "写剧本", "时间限制": "一周内"}
}
'''
        
        # 使用常规字符串构建提示词，避免f-string中的大括号问题
        prompt_template = f"""
你是一个专门从用户输入中提取用户偏好、兴趣和需求的AI助手。
请分析以下用户输入，提取用户的偏好、兴趣和需求，并以严格的JSON格式返回。

输出必须是有效的JSON格式，应包含以下字段：
- topics: 用户感兴趣的主题列表 (数组)
- preferences: 用户表达的偏好或喜好 (对象)
- goals: 用户希望达成的目标或需求 (数组)
- concerns: 用户可能存在的担忧或顾虑 (数组)
- context: 用户提供的上下文信息 (对象)

如果没有提取到特定字段的信息，请使用空数组[]或空对象{{}}。

用户输入:
{user_input}

请只返回JSON对象，不要包含任何其他文本、解释、标记或前缀。

示例响应格式:
"""
        
        # 组合提示词和示例
        return prompt_template + example_json
    
    @staticmethod
    def build_script_planning_prompt(context: Dict[str, Any]) -> str:
        """构建剧本规划提示词
        
        Args:
            context: 剧本上下文信息
            
        Returns:
            提示词
        """
        genre = context.get("genre", "未指定")
        theme = context.get("theme", "未指定")
        characters = context.get("characters", [])
        setting = context.get("setting", "未指定")
        duration = context.get("duration", "未指定")
        
        characters_str = "\n".join([f"- {char}" for char in characters]) if characters else "未指定"
        
        return f"""
请为以下剧本需求创建一个详细的规划方案：

类型: {genre}
主题: {theme}
角色:
{characters_str}
场景设定: {setting}
时长: {duration}

规划应包括:
1. 故事大纲 (包括三幕结构的关键点)
2. 主要角色的发展轨迹
3. 场景列表和简要描述
4. 主要冲突和解决方式
5. 预计观众反应和情感体验
"""
    
    @staticmethod
    def build_content_moderation_prompt(user_input: str) -> str:
        """构建内容审核提示词
        
        Args:
            user_input: 用户输入
            
        Returns:
            提示词
        """
        return f"""
分析以下用户输入，判断其是否包含不适当内容。输出应为JSON格式，包含以下字段：
- is_appropriate: 布尔值，表示内容是否适当
- concerns: 列表，包含发现的潜在问题(如有)
- suggestion: 如何以适当方式回应用户的建议(如有必要)

用户输入:
{user_input}
"""
    
    @staticmethod
    def build_role_consistency_evaluation_prompt(history: List[Dict[str, str]], persona: PersonaConfig) -> str:
        """构建角色一致性评估提示词
        
        Args:
            history: 对话历史
            persona: 人设配置
            
        Returns:
            提示词
        """
        role = persona.role
        style = persona.style
        
        # 构建对话历史文本
        conversation = ""
        for msg in history:
            if msg["role"] == "user":
                conversation += f"用户: {msg['content']}\n"
            elif msg["role"] == "assistant":
                conversation += f"助手: {msg['content']}\n"
        
        return f"""
你需要评估以下对话中，助手是否始终保持了作为"{role}"的角色特性和风格一致性。

角色风格要求:
{style}

对话历史:
{conversation}

请分析助手的回复是否符合角色设定，是否存在角色特性不一致的问题。输出应为JSON格式，包含以下字段:
- consistency_score: 1-10的分数，表示角色一致性水平
- strengths: 列表，表示哪些方面体现了良好的角色一致性
- weaknesses: 列表，表示哪些方面存在角色不一致
- suggestions: 如何改进角色表现的建议
"""

    @staticmethod
    def build_script_plan_param_prompt(user_input: str) -> str:
        return f"""
请从下面的用户输入中，提取剧本大纲所需的参数，输出JSON格式，字段包括：genre, theme, characters, setting, duration。
用户输入：{user_input}
输出示例：{{\"genre\": \"...\", \"theme\": \"...\", \"characters\": [\"...\"], \"setting\": \"...\", \"duration\": \"...\"}}
请只返回JSON对象，不要包含任何其他文本、解释、标记或前缀。如果无法提取某项参数，请用空字符串或空数组，不要省略字段。
"""

    @staticmethod
    def build_character_profile_param_prompt(user_input: str) -> str:
        return f"""
请从下面的用户输入中，提取角色档案所需的参数，输出JSON格式，字段包括：name, age, background, personality, goals。
用户输入：{user_input}
输出示例：{{\"name\": \"...\", \"age\": \"...\", \"background\": \"...\", \"personality\": \"...\", \"goals\": \"...\"}}
请只返回JSON对象，不要包含任何其他文本、解释、标记或前缀。如果无法提取某项参数，请用空字符串或空数组，不要省略字段。
"""

    @staticmethod
    def build_dialogue_param_prompt(user_input: str) -> str:
        return f"""
请从下面的用户输入中，提取对话生成所需的参数，输出JSON格式，字段包括：characters, scene, situation, tone, length。
用户输入：{user_input}
输出示例：{{\"characters\": [\"...\"], \"scene\": \"...\", \"situation\": \"...\", \"tone\": \"...\", \"length\": \"...\"}}
请只返回JSON对象，不要包含任何其他文本、解释、标记或前缀。如果无法提取某项参数，请用空字符串或空数组，不要省略字段。
"""

    @staticmethod
    def build_code_analysis_param_prompt(user_input: str) -> str:
        """构建代码分析参数提取提示词
        
        Args:
            user_input: 用户输入
            
        Returns:
            提示词
        """
        return f"""
请从下面的用户输入中，提取代码分析所需的参数，输出JSON格式，字段包括：code, language, focus。
用户输入：{user_input}
输出示例：{{"code": "def hello(): print('Hello world')", "language": "python", "focus": "代码质量"}}
请只返回JSON对象，不要包含任何其他文本、解释、标记或前缀。如果无法提取某项参数，请用空字符串，不要省略字段。
如果用户没有提供具体的代码，请将code字段留空，我们会在后续对话中请求用户提供。
"""

    @staticmethod
    def build_code_improvement_param_prompt(user_input: str) -> str:
        """构建代码优化参数提取提示词
        
        Args:
            user_input: 用户输入
            
        Returns:
            提示词
        """
        return f"""
请从下面的用户输入中，提取代码优化所需的参数，输出JSON格式，字段包括：code, language, improvement_type。
用户输入：{user_input}
输出示例：{{"code": "for i in range(len(arr)): print(arr[i])", "language": "python", "improvement_type": "性能优化"}}
请只返回JSON对象，不要包含任何其他文本、解释、标记或前缀。如果无法提取某项参数，请用空字符串，不要省略字段。
如果用户没有提供具体的代码，请将code字段留空，我们会在后续对话中请求用户提供。
"""

    @staticmethod
    def build_code_diagnosis_param_prompt(user_input: str) -> str:
        """构建代码问题诊断参数提取提示词
        
        Args:
            user_input: 用户输入
            
        Returns:
            提示词
        """
        return f"""
请从下面的用户输入中，提取代码问题诊断所需的参数，输出JSON格式，字段包括：code, error_message, language。
用户输入：{user_input}
输出示例：{{"code": "def calc(): return 10/0", "error_message": "ZeroDivisionError: division by zero", "language": "python"}}
请只返回JSON对象，不要包含任何其他文本、解释、标记或前缀。如果无法提取某项参数，请用空字符串，不要省略字段。
如果用户没有提供具体的代码或错误信息，请将相应字段留空，我们会在后续对话中请求用户提供。
"""

    @staticmethod
    def build_learning_plan_param_prompt(user_input: str) -> str:
        """构建学习计划参数提取提示词
        
        Args:
            user_input: 用户输入
            
        Returns:
            提示词
        """
        return f"""
请从下面的用户输入中，提取编程学习计划所需的参数，输出JSON格式，字段包括：language, current_level, learning_goal, time_available, interests。
用户输入：{user_input}
输出示例：{{"language": "Python", "current_level": "初学者", "learning_goal": "开发网站", "time_available": "每周10小时", "interests": "数据分析"}}
请只返回JSON对象，不要包含任何其他文本、解释、标记或前缀。如果无法提取某项参数，请用空字符串，不要省略字段。
""" 