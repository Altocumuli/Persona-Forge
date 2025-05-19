"""
工具调用跟踪器
"""
from typing import Dict, List, Any, Optional
import time
import json


class ToolTrace:
    """单个工具调用的跟踪记录"""
    
    def __init__(self, tool_name: str, inputs: Dict[str, Any]):
        """初始化工具调用跟踪
        
        Args:
            tool_name: 工具名称
            inputs: 工具输入参数
        """
        self.tool_name = tool_name
        self.inputs = inputs
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.outputs: Optional[Any] = None
        self.error: Optional[str] = None
        self.status = "running"  # running, completed, error
    
    def complete(self, outputs: Any) -> None:
        """完成工具调用
        
        Args:
            outputs: 工具输出
        """
        self.end_time = time.time()
        self.outputs = outputs
        self.status = "completed"
    
    def fail(self, error: str) -> None:
        """工具调用失败
        
        Args:
            error: 错误信息
        """
        self.end_time = time.time()
        self.error = error
        self.status = "error"
    
    def get_duration(self) -> float:
        """获取调用持续时间
        
        Returns:
            持续时间（秒）
        """
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            字典表示
        """
        result = {
            "tool_name": self.tool_name,
            "inputs": self.inputs,
            "start_time": self.start_time,
            "status": self.status,
            "duration": self.get_duration()
        }
        
        if self.end_time:
            result["end_time"] = self.end_time
        
        if self.outputs:
            result["outputs"] = self.outputs
        
        if self.error:
            result["error"] = self.error
        
        return result
    
    def to_html(self) -> str:
        """转换为HTML表示
        
        Returns:
            HTML格式的工具调用信息
        """
        status_color = {
            "running": "#1E88E5",  # 深蓝色
            "completed": "#2E7D32",  # 深绿色
            "error": "#D32F2F"  # 深红色
        }.get(self.status, "gray")
        
        inputs_str = json.dumps(self.inputs, ensure_ascii=False, indent=2)
        
        html = f'''<div class="tool-call" style="margin-bottom: 10px; border-left: 3px solid {status_color}; padding-left: 10px;">
<div style="font-weight: bold; color: #212121; font-size: 1em;">🔧 工具调用: {self.tool_name}</div>
<div style="margin: 5px 0; font-family: monospace; white-space: pre-wrap; font-size: 0.85em; color: #212121; background-color: #ECEFF1; padding: 5px; border-radius: 4px;">{inputs_str}</div>'''
        
        if self.status == "completed" and self.outputs:
            # 不再截断输出内容，而是依赖于UI的滚动功能
            outputs_str = str(self.outputs)
            
            html += f'''
<div style="margin-top: 5px;">
<span style="color: #2E7D32; font-weight: bold;">✓ 结果:</span>
<div style="margin: 5px 0; font-family: monospace; white-space: pre-wrap; font-size: 0.85em; color: #212121; background-color: #E8F5E9; padding: 5px; border-radius: 4px;">{outputs_str}</div>
</div>'''
        elif self.status == "error" and self.error:
            html += f'''
<div style="margin-top: 5px;">
<span style="color: #D32F2F; font-weight: bold;">✗ 错误:</span>
<div style="margin: 5px 0; font-family: monospace; white-space: pre-wrap; font-size: 0.85em; color: #212121; background-color: #FFEBEE; padding: 5px; border-radius: 4px;">{self.error}</div>
</div>'''
        elif self.status == "running":
            html += f'''
<div style="margin-top: 5px;">
<span style="color: #1E88E5; font-weight: bold;">⟳ 正在执行...</span>
</div>'''
        
        html += f'''
<div style="font-size: 0.8em; color: #616161; margin-top: 5px;">
耗时: {self.get_duration():.2f}秒
</div>
</div>'''
        
        return html


class ToolTracker:
    """工具调用跟踪器"""
    
    def __init__(self, update_callback=None):
        """初始化工具调用跟踪器
        
        Args:
            update_callback: 工具调用状态更新的回调函数，接收HTML报告作为参数
        """
        self.traces: List[ToolTrace] = []
        self.active_trace: Optional[ToolTrace] = None
        self.update_callback = update_callback
    
    def set_update_callback(self, callback):
        """设置更新回调函数
        
        Args:
            callback: 回调函数，接收HTML报告作为参数
        """
        self.update_callback = callback
    
    def start_trace(self, tool_name: str, inputs: Dict[str, Any]) -> ToolTrace:
        """开始跟踪工具调用
        
        Args:
            tool_name: 工具名称
            inputs: 工具输入参数
            
        Returns:
            工具调用跟踪对象
        """
        trace = ToolTrace(tool_name, inputs)
        self.traces.append(trace)
        self.active_trace = trace
        
        # 触发回调，通知外部工具调用状态更新
        if self.update_callback:
            self.update_callback(self.get_html_report())
            
        return trace
    
    def complete_trace(self, outputs: Any) -> None:
        """完成当前工具调用
        
        Args:
            outputs: 工具输出
        """
        if self.active_trace:
            self.active_trace.complete(outputs)
            self.active_trace = None
            
            # 触发回调，通知外部工具调用状态更新
            if self.update_callback:
                self.update_callback(self.get_html_report())
    
    def fail_trace(self, error: str) -> None:
        """当前工具调用失败
        
        Args:
            error: 错误信息
        """
        if self.active_trace:
            self.active_trace.fail(error)
            self.active_trace = None
            
            # 触发回调，通知外部工具调用状态更新
            if self.update_callback:
                self.update_callback(self.get_html_report())
    
    def get_all_traces(self) -> List[ToolTrace]:
        """获取所有工具调用跟踪
        
        Returns:
            工具调用跟踪列表
        """
        return self.traces
    
    def get_html_report(self) -> str:
        """获取HTML格式的报告
        
        Returns:
            HTML报告
        """
        if not self.traces:
            return "<div>没有工具调用记录</div>"
        
        html = "<div class='tool-tracker'>"
        for trace in self.traces:
            html += trace.to_html()
        html += "</div>"
        
        return html
    
    def clear(self) -> None:
        """清空跟踪记录"""
        self.traces = []
        self.active_trace = None
        
        # 触发回调，通知外部工具调用状态已清空
        if self.update_callback:
            self.update_callback(self.get_html_report()) 