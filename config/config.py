"""
套壳大模型系统基础配置文件
"""
import os
from dotenv import load_dotenv
import yaml
from pathlib import Path

# 加载环境变量
load_dotenv()

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent

# 人设配置目录
PERSONAS_DIR = ROOT_DIR / "config" / "personas"

# 默认LLM配置
DEFAULT_LLM_CONFIG = {
    "model_name": "qwen-turbo",  # 默认使用的模型
    "temperature": 0.7,     # 温度参数，控制创造性
    "max_tokens": 1000,     # 单次生成的最大token数
    "top_p": 0.95,          # 核采样参数
    "frequency_penalty": 0.0,  # 控制重复度
    "presence_penalty": 0.0,   # 控制话题覆盖度
    "streaming": True,      # 启用流式输出
}

# API密钥 (优先从环境变量读取)
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_API_BASE = os.getenv("DASHSCOPE_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")

# 系统提示词模板
SYSTEM_PROMPT_TEMPLATE = """
你现在扮演{role}。

{description}

你应该遵守以下行为准则：
{guidelines}

你的回复风格应该是：
{style}

在回复中，你需要始终保持角色一致性，不要透露你是一个AI或语言模型。
"""

def load_persona(persona_name):
    """加载特定人设配置"""
    persona_path = PERSONAS_DIR / f"{persona_name}.yaml"
    if not persona_path.exists():
        raise FileNotFoundError(f"找不到人设配置文件: {persona_path}")
    
    with open(persona_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_persona(persona_name, persona_data):
    """保存人设配置"""
    PERSONAS_DIR.mkdir(parents=True, exist_ok=True)
    persona_path = PERSONAS_DIR / f"{persona_name}.yaml"
    
    with open(persona_path, "w", encoding="utf-8") as f:
        yaml.dump(persona_data, f, allow_unicode=True, sort_keys=False) 