"""
人设封装类，用于管理模型的角色扮演行为
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
import os
from pathlib import Path
import yaml

class PersonaExample(BaseModel):
    """对话示例，用于few-shot学习"""
    user: str
    assistant: str

class PersonaConfig(BaseModel):
    """人设配置"""
    name: str = Field(..., description="人设名称")
    role: str = Field(..., description="扮演的角色")
    description: str = Field(..., description="详细的角色描述")
    guidelines: str = Field(..., description="行为准则")
    style: str = Field(..., description="回复风格")
    examples: Optional[List[PersonaExample]] = Field(None, description="对话示例")
    llm_config: Optional[Dict[str, Any]] = Field(None, description="LLM特定配置参数")
    
    def get_system_prompt(self) -> str:
        """生成系统提示词"""
        from config.config import SYSTEM_PROMPT_TEMPLATE
        
        prompt = SYSTEM_PROMPT_TEMPLATE.format(
            role=self.role,
            description=self.description,
            guidelines=self.guidelines,
            style=self.style
        )
        return prompt

class PersonaManager:
    """人设管理器，负责加载、保存和管理人设配置"""
    
    def __init__(self, personas_dir: Union[str, Path]):
        """初始化人设管理器
        
        Args:
            personas_dir: 人设配置文件目录
        """
        self.personas_dir = Path(personas_dir)
        if not self.personas_dir.exists():
            os.makedirs(self.personas_dir, exist_ok=True)
        
        self._personas: Dict[str, PersonaConfig] = {}
        self._load_all_personas()
    
    def _load_all_personas(self):
        """加载所有可用的人设配置"""
        for file_path in self.personas_dir.glob('*.yaml'):
            try:
                persona_name = file_path.stem
                self._personas[persona_name] = self.load_persona(persona_name)
            except Exception as e:
                print(f"加载人设 {file_path} 时出错: {e}")
    
    def load_persona(self, persona_name: str) -> PersonaConfig:
        """加载特定人设配置
        
        Args:
            persona_name: 人设名称
            
        Returns:
            人设配置对象
        """
        file_path = self.personas_dir / f"{persona_name}.yaml"
        if not file_path.exists():
            raise FileNotFoundError(f"找不到人设配置文件: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            
        # 处理示例数据格式转换
        if "examples" in data and data["examples"]:
            examples = []
            for example in data["examples"]:
                examples.append(PersonaExample(**example))
            data["examples"] = examples
            
        return PersonaConfig(**data)
    
    def save_persona(self, persona: PersonaConfig):
        """保存人设配置
        
        Args:
            persona: 人设配置对象
        """
        # 转换为字典
        data = persona.model_dump()
        
        # 处理示例数据序列化
        if "examples" in data and data["examples"]:
            examples = []
            for example in data["examples"]:
                examples.append({
                    "user": example["user"],
                    "assistant": example["assistant"]
                })
            data["examples"] = examples
        
        file_path = self.personas_dir / f"{persona.name}.yaml"
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)
        
        # 更新缓存
        self._personas[persona.name] = persona
    
    def create_persona(self, 
                      name: str, 
                      role: str, 
                      description: str, 
                      guidelines: str, 
                      style: str,
                      examples: Optional[List[Dict[str, str]]] = None,
                      llm_config: Optional[Dict[str, Any]] = None) -> PersonaConfig:
        """创建新的人设
        
        Args:
            name: 人设名称
            role: 扮演的角色
            description: 详细的角色描述
            guidelines: 行为准则
            style: 回复风格
            examples: 对话示例列表
            llm_config: LLM特定配置参数
            
        Returns:
            创建的人设配置对象
        """
        # 处理示例数据
        examples_obj = None
        if examples:
            examples_obj = [PersonaExample(**example) for example in examples]
        
        # 创建人设配置
        persona = PersonaConfig(
            name=name,
            role=role,
            description=description,
            guidelines=guidelines,
            style=style,
            examples=examples_obj,
            llm_config=llm_config
        )
        
        # 保存人设
        self.save_persona(persona)
        
        return persona
    
    def list_personas(self) -> List[str]:
        """列出所有可用的人设名称
        
        Returns:
            人设名称列表
        """
        return list(self._personas.keys())
    
    def get_persona(self, persona_name: str) -> Optional[PersonaConfig]:
        """获取特定人设配置
        
        Args:
            persona_name: 人设名称
            
        Returns:
            人设配置对象，如果不存在则返回None
        """
        if persona_name in self._personas:
            return self._personas[persona_name]
        
        try:
            persona = self.load_persona(persona_name)
            self._personas[persona_name] = persona
            return persona
        except FileNotFoundError:
            return None
        
    def delete_persona(self, persona_name: str) -> bool:
        """删除特定人设配置
        
        Args:
            persona_name: 人设名称
            
        Returns:
            是否成功删除
        """
        file_path = self.personas_dir / f"{persona_name}.yaml"
        if not file_path.exists():
            return False
        
        try:
            os.remove(file_path)
            if persona_name in self._personas:
                del self._personas[persona_name]
            return True
        except Exception:
            return False 