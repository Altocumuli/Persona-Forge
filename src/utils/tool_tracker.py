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
        
        status_icon = {
            "running": "&#8635;",  # 循环箭头
            "completed": "&#10004;",  # 勾
            "error": "&#10060;"  # 错
        }.get(self.status, "&#8226;")  # 圆点
        
        # 美化输入参数显示
        inputs_str = json.dumps(self.inputs, ensure_ascii=False, indent=2)
        
        # 根据状态设置卡片样式
        card_shadow = "0 2px 4px rgba(0,0,0,0.1)"
        if self.status == "completed":
            card_bg = "#F9FBF9"
            header_bg = "#EDF7ED"
        elif self.status == "error":
            card_bg = "#FEF8F8"
            header_bg = "#FDECEC" 
        else:
            card_bg = "#F5F9FF"
            header_bg = "#E3F2FD"
        
        # 为每个工具调用生成唯一ID，避免DOM和JS函数冲突
        tool_id = f"tool_{int(self.start_time * 1000)}"
        
        # 生成卡片头部
        html = f"""
<div class="tool-call-card" id="{tool_id}_card" style="margin-bottom: 16px; border-radius: 8px; overflow: hidden; box-shadow: {card_shadow}; background: {card_bg}; border: 1px solid rgba(0,0,0,0.08);">
    <div class="tool-header" style="padding: 12px 16px; background: {header_bg}; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(0,0,0,0.05);">
        <div style="display: flex; align-items: center;">
            <span style="margin-right: 8px; font-size: 18px;">🔧</span>
            <span style="font-weight: 600; color: #424242; font-size: 0.95em;">{self.tool_name}</span>
        </div>
        <div style="display: flex; align-items: center;">
            <span style="color: {status_color}; font-weight: 500; font-size: 1em; margin-right: 4px;">{status_icon}</span>
            <span style="color: {status_color}; font-size: 0.85em;">{self.status.capitalize()}</span>
        </div>
    </div>
    <div class="tool-body" style="padding: 16px;">
        <div style="margin-bottom: 12px;">
            <div style="font-weight: 500; color: #616161; font-size: 0.85em; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px;">输入参数</div>
            <div style="font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace; white-space: pre-wrap; font-size: 0.9em; line-height: 1.5; color: #424242; background-color: rgba(0,0,0,0.03); padding: 12px; border-radius: 6px; overflow-x: auto; max-height: 200px; overflow-y: auto;">{inputs_str}</div>
        </div>"""
        
        # 处理已完成状态的输出
        if self.status == "completed" and self.outputs:
            # 格式化输出，根据输出类型选择合适的显示方式
            if isinstance(self.outputs, str) and len(self.outputs) > 500:
                # 长文本输出，添加可折叠区域
                outputs_preview = self.outputs[:500] + "..."
                outputs_full = self.outputs.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n")
                html += f"""
        <div style="margin-bottom: 12px;">
            <div style="font-weight: 500; color: #616161; font-size: 0.85em; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; display: flex; justify-content: space-between; align-items: center;">
                <span>输出结果</span>
                <button onclick="window.toggleToolOutput('{tool_id}')" style="background: none; border: none; color: #1E88E5; cursor: pointer; font-size: 0.85em; padding: 2px 6px;">展开完整内容</button>
            </div>
            <div id="{tool_id}_preview" style="display: block; font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace; white-space: pre-wrap; font-size: 0.9em; line-height: 1.5; color: #424242; background-color: rgba(46,125,50,0.05); padding: 12px; border-radius: 6px; overflow-x: auto; max-height: 200px; overflow-y: auto;">{outputs_preview}</div>
            <div id="{tool_id}_full" style="display: none; font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace; white-space: pre-wrap; font-size: 0.9em; line-height: 1.5; color: #424242; background-color: rgba(46,125,50,0.05); padding: 12px; border-radius: 6px; overflow-x: auto; max-height: 800px; overflow-y: auto;"></div>
            <script>
                document.getElementById('{tool_id}_full').textContent = "{outputs_full}";
            </script>
        </div>"""
            else:
                # 常规输出
                try:
                    # 尝试将JSON字符串转换为格式化显示
                    if isinstance(self.outputs, str) and (self.outputs.startswith('{') or self.outputs.startswith('[')):
                        json_obj = json.loads(self.outputs)
                        outputs_str = json.dumps(json_obj, ensure_ascii=False, indent=2)
                    else:
                        outputs_str = str(self.outputs)
                except:
                    outputs_str = str(self.outputs)
                
                html += f"""
        <div style="margin-bottom: 12px;">
            <div style="font-weight: 500; color: #616161; font-size: 0.85em; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px;">输出结果</div>
            <div style="font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace; white-space: pre-wrap; font-size: 0.9em; line-height: 1.5; color: #424242; background-color: rgba(46,125,50,0.05); padding: 12px; border-radius: 6px; overflow-x: auto; max-height: 800px; overflow-y: auto;">{outputs_str}</div>
        </div>"""
        
        # 处理错误状态
        elif self.status == "error" and self.error:
            html += f"""
        <div style="margin-bottom: 12px;">
            <div style="font-weight: 500; color: #616161; font-size: 0.85em; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px;">错误信息</div>
            <div style="font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace; white-space: pre-wrap; font-size: 0.9em; line-height: 1.5; color: #D32F2F; background-color: rgba(211,47,47,0.05); padding: 12px; border-radius: 6px; overflow-x: auto; max-height: 800px; overflow-y: auto;">{self.error}</div>
        </div>"""
        
        # 处理正在运行状态
        elif self.status == "running":
            html += """
        <div style="margin-top: 12px; display: flex; align-items: center;">
            <div class="loading-spinner" style="width: 18px; height: 18px; border: 2px solid #E0E0E0; border-top: 2px solid #1E88E5; border-radius: 50%; animation: spin 1.5s linear infinite; margin-right: 8px;"></div>
            <span style="color: #1E88E5; font-weight: 500;">正在执行中...</span>
        </div>
        <style>
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        </style>"""
        
        # 添加卡片底部
        html += f"""
        <div style="display: flex; justify-content: flex-end; font-size: 0.8em; color: #757575; margin-top: 8px;">
            耗时: {self.get_duration():.2f}秒
        </div>
    </div>
</div>"""
        
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
        
        # 添加全局JavaScript函数，用于切换输出显示
        js_script = """
<script>
// 全局工具输出切换函数
window.toggleToolOutput = function(toolId) {
    const preview = document.getElementById(toolId + '_preview');
    const full = document.getElementById(toolId + '_full');
    const button = document.querySelector(`#${toolId}_card button`);
    
    if (preview.style.display === 'none') {
        preview.style.display = 'block';
        full.style.display = 'none';
        button.textContent = '展开完整内容';
    } else {
        preview.style.display = 'none';
        full.style.display = 'block';
        button.textContent = '收起';
    }
}
</script>
        """
        
        html = f"<div class='tool-tracker'>{js_script}"
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