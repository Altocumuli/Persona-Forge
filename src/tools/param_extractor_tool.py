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