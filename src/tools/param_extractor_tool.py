from src.utils.prompt_builder import PromptBuilder
import json
import re

class ParamExtractor:
    def __init__(self, llm):
        self.llm = llm

    def _extract_json(self, text):
        # 尝试用正则提取第一个JSON对象
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                return {}
        return {}

    def extract_script_plan_params(self, user_input):
        prompt = PromptBuilder.build_script_plan_param_prompt(user_input)
        response = self.llm.invoke(prompt)
        print('参数提取LLM原始输出:', response)  # 调试用
        result = self._extract_json(response)
        if not result:
            print('参数提取失败，返回空')
        return result

    def extract_character_profile_params(self, user_input):
        prompt = PromptBuilder.build_character_profile_param_prompt(user_input)
        response = self.llm.invoke(prompt)
        print('参数提取LLM原始输出:', response)
        result = self._extract_json(response)
        if not result:
            print('参数提取失败，返回空')
        return result

    def extract_dialogue_params(self, user_input):
        prompt = PromptBuilder.build_dialogue_param_prompt(user_input)
        response = self.llm.invoke(prompt)
        print('参数提取LLM原始输出:', response)
        result = self._extract_json(response)
        if not result:
            print('参数提取失败，返回空')
        return result
        
    def extract_code_analysis_params(self, user_input):
        """从用户输入中提取代码分析所需的参数
        
        Args:
            user_input: 用户输入
            
        Returns:
            包含code, language, focus的字典
        """
        prompt = PromptBuilder.build_code_analysis_param_prompt(user_input)
        response = self.llm.invoke(prompt)
        print('代码分析参数提取LLM原始输出:', response)
        result = self._extract_json(response)
        if not result:
            print('代码分析参数提取失败，返回空')
        return result
    
    def extract_code_improvement_params(self, user_input):
        """从用户输入中提取代码优化所需的参数
        
        Args:
            user_input: 用户输入
            
        Returns:
            包含code, language, improvement_type的字典
        """
        prompt = PromptBuilder.build_code_improvement_param_prompt(user_input)
        response = self.llm.invoke(prompt)
        print('代码优化参数提取LLM原始输出:', response)
        result = self._extract_json(response)
        if not result:
            print('代码优化参数提取失败，返回空')
        return result
    
    def extract_code_diagnosis_params(self, user_input):
        """从用户输入中提取代码问题诊断所需的参数
        
        Args:
            user_input: 用户输入
            
        Returns:
            包含code, error_message, language的字典
        """
        prompt = PromptBuilder.build_code_diagnosis_param_prompt(user_input)
        response = self.llm.invoke(prompt)
        print('代码诊断参数提取LLM原始输出:', response)
        result = self._extract_json(response)
        if not result:
            print('代码诊断参数提取失败，返回空')
        return result
    
    def extract_learning_plan_params(self, user_input):
        """从用户输入中提取学习计划所需的参数
        
        Args:
            user_input: 用户输入
            
        Returns:
            包含language, current_level, learning_goal, time_available, interests的字典
        """
        prompt = PromptBuilder.build_learning_plan_param_prompt(user_input)
        response = self.llm.invoke(prompt)
        print('学习计划参数提取LLM原始输出:', response)
        result = self._extract_json(response)
        if not result:
            print('学习计划参数提取失败，返回空')
        return result 