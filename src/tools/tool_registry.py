"""
工具意图注册与调度模块
"""
from typing import Callable, List, Dict, Any

class ToolIntent:
    def __init__(self, name: str, keywords: List[str], param_extractor: Callable[[str], dict], tool_func: Callable[[dict], Any], description: str = ""):
        self.name = name
        self.keywords = keywords
        self.param_extractor = param_extractor
        self.tool_func = tool_func
        self.description = description

    def match(self, user_input: str) -> bool:
        return any(kw in user_input for kw in self.keywords)

    def extract_params(self, user_input: str) -> dict:
        return self.param_extractor(user_input)

    def call(self, params: dict) -> Any:
        return self.tool_func(params)

class ToolIntentRegistry:
    def __init__(self):
        self.intents: List[ToolIntent] = []

    def register(self, intent: ToolIntent):
        self.intents.append(intent)

    def detect_and_run(self, user_input: str) -> List[Dict[str, Any]]:
        traces = []
        for intent in self.intents:
            if intent.match(user_input):
                params = intent.extract_params(user_input)
                try:
                    result = intent.call(params)
                    traces.append({
                        "intent": intent.name,
                        "params": params,
                        "result": result,
                        "status": "success",
                        "description": intent.description
                    })
                except Exception as e:
                    traces.append({
                        "intent": intent.name,
                        "params": params,
                        "error": str(e),
                        "status": "fail",
                        "description": intent.description
                    })
        return traces 