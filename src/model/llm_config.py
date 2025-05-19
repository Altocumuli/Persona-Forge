"""
大语言模型配置和管理
"""
from typing import Dict, Any, List, Optional, Union, Callable
import os
from config.config import DEFAULT_LLM_CONFIG, DASHSCOPE_API_KEY, DASHSCOPE_API_BASE
from langchain_community.llms.tongyi import Tongyi
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import Runnable
from langchain_core.output_parsers import StrOutputParser
from src.model.persona import PersonaConfig


class LLMManager:
    """LLM管理器，负责初始化和管理语言模型"""
    
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None):
        """初始化LLM管理器
        
        Args:
            api_key: DashScope API密钥，如果为None则使用环境变量或配置
            api_base: DashScope API基础URL，如果为None则使用环境变量或配置
        """
        self.api_key = api_key or DASHSCOPE_API_KEY
        self.api_base = api_base or DASHSCOPE_API_BASE
        
        if not self.api_key:
            raise ValueError("缺少API密钥，请设置DASHSCOPE_API_KEY环境变量或在初始化时提供")
    
    def create_llm(self, model_config: Optional[Dict[str, Any]] = None) -> Tongyi:
        """创建LLM实例
        
        Args:
            model_config: 模型配置参数，如果为None则使用默认配置
            
        Returns:
            Tongyi实例
        """
        # 合并默认配置和自定义配置
        config = DEFAULT_LLM_CONFIG.copy()
        if model_config:
            config.update(model_config)
        
        # 创建LLM实例
        llm = Tongyi(
            model_name=config.get("model_name", "qwen-turbo"),
            dashscope_api_key=self.api_key,
            streaming=config.get("streaming", True),  # 默认启用流式输出
            model_kwargs={
                "temperature": config.get("temperature", 0.7),
                "max_tokens": config.get("max_tokens", 2000),
                "top_p": config.get("top_p", 0.95),
                "frequency_penalty": config.get("frequency_penalty", 0.0),
                "presence_penalty": config.get("presence_penalty", 0.0),
            },
            endpoint_url=self.api_base
        )
        
        return llm
    
    def create_persona_chain(self, 
                            persona: PersonaConfig, 
                            memory: Optional[Any] = None,
                            tools: Optional[List[Any]] = None) -> Runnable:
        """创建带有人设的对话链
        
        Args:
            persona: 人设配置
            memory: 对话记忆组件
            tools: 可用工具列表
            
        Returns:
            对话链
        """
        # 创建LLM实例
        llm = self.create_llm(persona.llm_config)
        
        # 准备系统提示词
        system_prompt = persona.get_system_prompt()
        
        # 创建提示模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])
        
        # 创建对话链
        chain = prompt | llm | StrOutputParser()
        
        return chain
    
    def create_chat_messages(self, 
                           system_prompt: str, 
                           conversation_history: List[Dict[str, str]]) -> List[Union[SystemMessage, HumanMessage, AIMessage]]:
        """从对话历史创建消息列表
        
        Args:
            system_prompt: 系统提示词
            conversation_history: 对话历史记录
            
        Returns:
            消息列表
        """
        messages = [SystemMessage(content=system_prompt)]
        
        for message in conversation_history:
            if message["role"] == "user":
                messages.append(HumanMessage(content=message["content"]))
            elif message["role"] == "assistant":
                messages.append(AIMessage(content=message["content"]))
        
        return messages
    
    def generate_response(self, 
                         persona: PersonaConfig, 
                         user_input: str,
                         conversation_history: Optional[List[Dict[str, str]]] = None,
                         streaming_callback=None,
                         system_prompt: Optional[str] = None) -> str:
        """生成响应
        
        Args:
            persona: 人设配置
            user_input: 用户输入
            conversation_history: 对话历史记录
            streaming_callback: 流式输出的回调函数
            system_prompt: 自定义系统提示词，如果提供则使用此提示词
            
        Returns:
            助手响应
        """
        # 创建LLM实例
        llm = self.create_llm(persona.llm_config)
        
        # 创建完整的提示信息
        if system_prompt is None:
            system_prompt = persona.get_system_prompt()
        
        # 构建消息历史文本格式
        # DashScope的兼容模式使用文本格式而非消息列表
        prompt_text = system_prompt + "\n\n"
        
        # 添加对话历史
        if conversation_history:
            for message in conversation_history:
                if message["role"] == "user":
                    prompt_text += f"用户: {message['content']}\n"
                elif message["role"] == "assistant":
                    prompt_text += f"助手: {message['content']}\n"
        
        # 添加当前用户输入
        prompt_text += f"用户: {user_input}\n助手: "
        
        # 生成响应
        if streaming_callback:
            # 使用流式输出
            response_text = ""
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    for chunk in llm.stream(prompt_text):
                        if chunk:  # 确保chunk不为空
                            streaming_callback(chunk)
                            response_text += chunk
                    break  # 如果成功完成，跳出重试循环
                except Exception as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        print(f"流式输出失败，已达到最大重试次数: {e}")
                        break
                    print(f"流式输出出错，正在重试 ({retry_count}/{max_retries}): {e}")
                    continue
            
            return response_text
        else:
            # 不使用流式输出
            try:
                response = llm.invoke(prompt_text)
                return response
            except Exception as e:
                print(f"生成响应时出错: {e}")
                return f"抱歉，生成响应时出现错误: {str(e)}" 