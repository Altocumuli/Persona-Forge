"""
对话上下文管理器，负责维护对话历史和状态
"""
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
import os
import time


class ContextManager:
    """对话上下文管理器"""
    
    def __init__(self, session_id: str, history_dir: Optional[Path] = None):
        """初始化上下文管理器
        
        Args:
            session_id: 会话ID
            history_dir: 历史记录保存目录
        """
        self.session_id = session_id
        self.history: List[Dict[str, str]] = []
        self.metadata: Dict[str, Any] = {
            "session_id": session_id,
            "created_at": time.time(),
            "last_updated": time.time(),
            "message_count": 0
        }
        
        # 设置历史记录目录
        if history_dir:
            self.history_dir = Path(history_dir)
        else:
            # 默认在项目根目录下的history文件夹
            self.history_dir = Path(__file__).parent.parent.parent / "history"
        
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.history_dir / f"{session_id}.json"
        
        # 尝试加载历史记录
        self._load_history()
    
    def add_message(self, role: str, content: str) -> None:
        """添加消息到历史记录
        
        Args:
            role: 消息角色 (user/assistant)
            content: 消息内容
        """
        # 添加消息
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time()
        }
        self.history.append(message)
        
        # 更新元数据
        self.metadata["last_updated"] = time.time()
        self.metadata["message_count"] += 1
        
        # 保存历史记录
        self._save_history()
    
    def get_history(self, max_messages: Optional[int] = None) -> List[Dict[str, str]]:
        """获取历史记录
        
        Args:
            max_messages: 最大消息数量，如果为None则返回所有消息
            
        Returns:
            历史记录列表
        """
        if max_messages is None:
            return self.history
        
        return self.history[-max_messages:]
    
    def clear_history(self) -> None:
        """清空历史记录"""
        self.history = []
        self.metadata["message_count"] = 0
        self.metadata["last_updated"] = time.time()
        self._save_history()
    
    def _save_history(self) -> None:
        """保存历史记录到文件"""
        data = {
            "metadata": self.metadata,
            "history": self.history
        }
        
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_history(self) -> None:
        """从文件加载历史记录"""
        if not self.history_file.exists():
            return
        
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.metadata = data.get("metadata", self.metadata)
            self.history = data.get("history", [])
        except Exception as e:
            print(f"加载历史记录时出错: {e}")


class SessionManager:
    """会话管理器，负责管理多个对话会话"""
    
    def __init__(self, history_dir: Optional[Path] = None):
        """初始化会话管理器
        
        Args:
            history_dir: 历史记录保存目录
        """
        # 设置历史记录目录
        if history_dir:
            self.history_dir = Path(history_dir)
        else:
            # 默认在项目根目录下的history文件夹
            self.history_dir = Path(__file__).parent.parent.parent / "history"
        
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        # 缓存当前活动的会话
        self.active_sessions: Dict[str, ContextManager] = {}
    
    def create_session(self, session_id: Optional[str] = None) -> ContextManager:
        """创建新会话
        
        Args:
            session_id: 会话ID，如果为None则自动生成
            
        Returns:
            上下文管理器
        """
        if session_id is None:
            session_id = f"session_{int(time.time())}"
        
        context = ContextManager(session_id, self.history_dir)
        self.active_sessions[session_id] = context
        
        return context
    
    def get_session(self, session_id: str) -> Optional[ContextManager]:
        """获取会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            上下文管理器，如果不存在则返回None
        """
        # 检查缓存
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # 检查文件系统
        session_file = self.history_dir / f"{session_id}.json"
        if session_file.exists():
            context = ContextManager(session_id, self.history_dir)
            self.active_sessions[session_id] = context
            return context
        
        return None
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功删除
        """
        # 从缓存中移除
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        # 从文件系统中删除
        session_file = self.history_dir / f"{session_id}.json"
        if session_file.exists():
            try:
                os.remove(session_file)
                return True
            except Exception:
                return False
        
        return False
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话
        
        Returns:
            会话元数据列表
        """
        sessions = []
        
        for file_path in self.history_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                metadata = data.get("metadata", {})
                sessions.append(metadata)
            except Exception as e:
                print(f"读取会话文件 {file_path} 时出错: {e}")
        
        # 按最后更新时间排序
        sessions.sort(key=lambda x: x.get("last_updated", 0), reverse=True)
        
        return sessions 