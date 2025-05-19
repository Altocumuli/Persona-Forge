"""
编程辅助工具，用于代码分析、优化建议和编程问题诊断
"""
from typing import Dict, Any, List, Optional
import json
import re
from langchain_core.tools import Tool
from langchain_community.llms.tongyi import Tongyi
from src.utils.prompt_builder import PromptBuilder


class CodeAnalyzerTool:
    """编程辅助工具，提供代码分析和优化建议"""
    
    def __init__(self, llm: Optional[Tongyi] = None, tracker=None):
        """初始化编程辅助工具
        
        Args:
            llm: 语言模型实例，如果为None则创建一个新实例
            tracker: 工具跟踪器实例
        """
        if llm is None:
            from config.config import DEFAULT_LLM_CONFIG, DASHSCOPE_API_KEY, DASHSCOPE_API_BASE
            self.llm = Tongyi(
                model_name=DEFAULT_LLM_CONFIG.get("model_name", "qwen-turbo"),
                dashscope_api_key=DASHSCOPE_API_KEY,
                model_kwargs={"temperature": 0.5},  # 使用较低的温度以确保代码分析的准确性
                endpoint_url=DASHSCOPE_API_BASE
            )
        else:
            self.llm = llm
        
        self.tracker = tracker
    
    def analyze_code(self, code_context: Dict[str, Any]) -> str:
        """分析代码结构和质量
        
        Args:
            code_context: 代码上下文信息，包含代码内容、语言等
            
        Returns:
            代码分析结果
        """
        # 如果有跟踪器，记录工具调用开始
        if self.tracker:
            self.tracker.start_trace("分析代码结构和质量", code_context)
        
        try:
            code = code_context.get("code", "")
            language = code_context.get("language", "python")
            focus = code_context.get("focus", "全面分析")  # 分析重点可以是"性能"、"可读性"、"安全性"等
            
            # 针对代码分析的提示词
            prompt = f"""
请分析以下{language}代码，重点关注{focus}：

```{language}
{code}
```

请提供以下分析：
1. 代码结构概述（主要组件和功能）
2. 代码质量评估（可读性、命名规范、注释等）
3. 潜在问题和风险
4. 优化建议和改进方向
5. 代码评分（1-10分）及总结评价

请使用清晰的章节格式组织你的分析，并提供具体的代码示例来支持你的建议。
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
            return f"分析代码时出错: {e}"
    
    def suggest_code_improvements(self, code_context: Dict[str, Any]) -> str:
        """为代码提供优化和改进建议
        
        Args:
            code_context: 代码上下文信息，包含代码内容、语言等
            
        Returns:
            优化建议
        """
        # 如果有跟踪器，记录工具调用开始
        if self.tracker:
            self.tracker.start_trace("提供代码优化建议", code_context)
        
        try:
            code = code_context.get("code", "")
            language = code_context.get("language", "python")
            improvement_type = code_context.get("improvement_type", "综合优化")  # 可以是"性能优化"、"可读性改进"、"安全加固"等
            
            # 针对代码优化的提示词
            prompt = f"""
请针对以下{language}代码，提供{improvement_type}方面的改进建议：

```{language}
{code}
```

请提供以下内容：
1. 可改进的具体部分（标注行号或代码片段）
2. 详细的改进建议和原因
3. 改进后的代码示例
4. 预期的改进效果

请注意保持代码的原有功能，同时使其更加高效、简洁、易于维护或安全。
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
            return f"提供优化建议时出错: {e}"
    
    def diagnose_code_issue(self, error_context: Dict[str, Any]) -> str:
        """诊断代码错误和问题
        
        Args:
            error_context: 错误上下文信息，包含代码、错误信息等
            
        Returns:
            问题诊断结果和修复建议
        """
        # 如果有跟踪器，记录工具调用开始
        if self.tracker:
            self.tracker.start_trace("诊断代码问题", error_context)
        
        try:
            code = error_context.get("code", "")
            error_message = error_context.get("error_message", "未提供错误信息")
            language = error_context.get("language", "python")
            
            # 针对错误诊断的提示词
            prompt = f"""
请诊断以下{language}代码中的问题：

```{language}
{code}
```

错误信息：
{error_message}

请提供以下内容：
1. 错误原因的详细解释
2. 问题所在的具体代码行或部分
3. 修复建议和解决方案
4. 修复后的代码示例
5. 防止类似错误的最佳实践建议

请确保您的解释对编程初学者友好，使用清晰的语言并避免过于专业的术语。
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
            return f"诊断代码问题时出错: {e}"
    
    def generate_learning_plan(self, learning_context: Dict[str, Any]) -> str:
        """生成个性化的编程学习计划
        
        Args:
            learning_context: 学习上下文信息，包含目标、当前水平等
            
        Returns:
            学习计划
        """
        # 如果有跟踪器，记录工具调用开始
        if self.tracker:
            self.tracker.start_trace("生成学习计划", learning_context)
        
        try:
            language = learning_context.get("language", "Python")
            current_level = learning_context.get("current_level", "初学者")  # 可以是"初学者"、"中级"、"高级"
            learning_goal = learning_context.get("learning_goal", "掌握基础")
            time_available = learning_context.get("time_available", "每周5小时")
            interests = learning_context.get("interests", "无特定兴趣")
            
            # 针对学习计划的提示词
            prompt = f"""
请为以下学习情况制定一个详细的编程学习计划：

编程语言: {language}
当前水平: {current_level}
学习目标: {learning_goal}
可用时间: {time_available}
兴趣领域: {interests}

请提供以下内容：
1. 为期4-8周的阶段性学习路线图
2. 每个阶段的具体学习目标和内容
3. 推荐的学习资源（书籍、在线课程、文档、练习平台等）
4. 实践项目建议（从简单到复杂）
5. 学习进度跟踪和自测方法
6. 常见学习误区和注意事项

请确保学习计划循序渐进，注重实践，并能保持学习动力。
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
            return f"生成学习计划时出错: {e}"
    
    def get_analyzer_tool(self) -> Tool:
        """获取代码分析工具的Tool实例"""
        return Tool(
            name="code_analyzer",
            func=self.analyze_code,
            description="分析代码结构和质量，提供全面评估",
            return_direct=True
        )
    
    def get_improvement_tool(self) -> Tool:
        """获取代码优化建议工具的Tool实例"""
        return Tool(
            name="code_improver",
            func=self.suggest_code_improvements,
            description="为代码提供优化和改进建议，使其更高效和可维护",
            return_direct=True
        )
    
    def get_diagnosis_tool(self) -> Tool:
        """获取代码问题诊断工具的Tool实例"""
        return Tool(
            name="code_diagnostics",
            func=self.diagnose_code_issue,
            description="诊断代码错误和问题，提供修复建议",
            return_direct=True
        )
    
    def get_learning_plan_tool(self) -> Tool:
        """获取学习计划生成工具的Tool实例"""
        return Tool(
            name="learning_plan_generator",
            func=self.generate_learning_plan,
            description="生成个性化的编程学习计划，提供学习路线和资源推荐",
            return_direct=True
        ) 