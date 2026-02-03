"""
本地 Jupyter 内核客户端 - 无需 Docker 直接执行代码
使用 jupyter_client 与本地 Jupyter 内核通信

Local Jupyter Kernel Client - Execute code directly without Docker
Uses jupyter_client to communicate with local Jupyter kernels
"""
import json
import logging
import queue
import atexit
from typing import Optional, Dict, Any

try:
    import jupyter_client
    JUPYTER_CLIENT_AVAILABLE = True
except ImportError:
    JUPYTER_CLIENT_AVAILABLE = False
    logging.warning("jupyter_client not installed. Local kernel execution will not be available.")

logging.basicConfig(level=logging.INFO)


class LocalJupyterKernel:
    """
    本地 Jupyter 内核执行器
    直接与本地 Jupyter 内核通信，无需 Docker 或 HTTP API
    """

    def __init__(self, conv_id: str, kernel_name: str = "python3"):
        """
        初始化本地 Jupyter 内核

        参数:
            conv_id: 会话ID，用于标识不同的执行会话
            kernel_name: 内核名称，默认为 python3
        """
        if not JUPYTER_CLIENT_AVAILABLE:
            raise ImportError(
                "jupyter_client package is required for local execution. "
                "Install it with: pip install jupyter_client ipykernel"
            )

        self.conv_id = conv_id
        self.kernel_name = kernel_name
        self.km = None  # KernelManager: 内核管理器
        self.kc = None  # KernelClient: 内核客户端
        self._initialized = False
        self._start_kernel()
        # 注册退出时自动清理
        atexit.register(self.shutdown)

    def _start_kernel(self):
        """启动新的 Jupyter 内核"""
        self.km = jupyter_client.KernelManager(kernel_name=self.kernel_name)
        self.km.start_kernel()
        self.kc = self.km.client()
        self.kc.start_channels()
        # 等待内核就绪，超时60秒
        self.kc.wait_for_ready(timeout=60)
        logging.info(f"Local Jupyter kernel started for conversation {self.conv_id}")

    def execute(self, code: str, timeout: int = 60) -> str:
        """
        在内核中执行代码并返回结果

        参数:
            code: 要执行的 Python 代码
            timeout: 执行超时时间（秒）

        返回:
            执行结果字符串
        """
        if not self.kc:
            self._start_kernel()

        # 发送执行请求
        msg_id = self.kc.execute(code)

        outputs = []
        execution_done = False

        while not execution_done:
            try:
                # 从 iopub 通道获取消息
                msg = self.kc.get_iopub_msg(timeout=timeout)
                msg_type = msg['msg_type']
                content = msg['content']

                # 忽略不属于当前请求的消息
                if msg['parent_header'].get('msg_id') != msg_id:
                    continue

                if msg_type == 'error':
                    # 收集错误回溯信息
                    traceback = '\n\n\n\n'.join(content.get('traceback', []))
                    outputs.append(self._strip_ansi(traceback))
                    execution_done = True

                elif msg_type == 'stream':
                    # 标准输出/错误流
                    outputs.append(content.get('text', ''))

                elif msg_type in ['execute_result', 'display_data']:
                    # 执行结果或显示数据
                    data = content.get('data', {})
                    if 'text/plain' in data:
                        outputs.append(data['text/plain'])
                    if 'image/png' in data:
                        # 将图片转为 Markdown 格式
                        outputs.append(f"![image](data:image/png;base64,{data['image/png']})")

                elif msg_type == 'status':
                    # 内核状态变为空闲表示执行完成
                    if content.get('execution_state') == 'idle':
                        execution_done = True

            except queue.Empty:
                return f"[Execution timed out ({timeout} seconds).]"
            except Exception as e:
                return f"[Execution error: {str(e)}]"

        if not outputs:
            return "[Code executed successfully with no output]"

        return ''.join(outputs)

    def _strip_ansi(self, text: str) -> str:
        """移除文本中的 ANSI 转义序列（终端颜色代码等）"""
        import re
        pattern = re.compile(r'\x1B\[\d+(;\d+){0,2}m')
        return pattern.sub('', text)

    def shutdown(self):
        """关闭内核，释放资源"""
        if self.kc:
            self.kc.stop_channels()
            self.kc = None
        if self.km:
            self.km.shutdown_kernel(now=True)
            self.km = None
        logging.info(f"Local kernel shutdown for conversation {self.conv_id}")


class LocalKernelClient:
    """
    本地内核客户端接口
    与 ClientJupyterKernel 接口兼容，可无缝切换
    """

    def __init__(self, conv_id: str):
        """
        初始化客户端

        参数:
            conv_id: 会话ID
        """
        self.conv_id = conv_id
        self.kernel = None
        self._new_kernel = True
        print(f"LocalKernelClient initialized with conv_id={conv_id}")

    def execute(self, code: str) -> str:
        """
        执行代码并返回结果

        参数:
            code: 要执行的代码

        返回:
            执行结果
        """
        if self.kernel is None:
            # 延迟创建内核，首次执行时才启动
            self.kernel = LocalJupyterKernel(self.conv_id)
            self._new_kernel = True
        else:
            self._new_kernel = False

        result = self.kernel.execute(code)
        return result

    def shutdown(self):
        """关闭内核"""
        if self.kernel:
            self.kernel.shutdown()
            self.kernel = None


class LocalKernelManager:
    """
    本地内核管理器（单例模式）
    管理多个本地内核，每个会话对应一个独立内核
    """

    _instance = None
    _kernels: Dict[str, LocalKernelClient] = {}

    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._kernels = {}
        return cls._instance

    @classmethod
    def get_client(cls, conv_id: str) -> LocalKernelClient:
        """
        获取或创建指定会话的内核客户端

        参数:
            conv_id: 会话ID

        返回:
            LocalKernelClient 实例
        """
        if conv_id not in cls._kernels:
            cls._kernels[conv_id] = LocalKernelClient(conv_id)
        return cls._kernels[conv_id]

    @classmethod
    def shutdown_all(cls):
        """关闭所有内核"""
        for conv_id, client in cls._kernels.items():
            client.shutdown()
        cls._kernels.clear()
        logging.info("All local kernels shutdown")


def get_local_kernel_client(conv_id: str) -> LocalKernelClient:
    """
    获取本地内核客户端的便捷函数

    参数:
        conv_id: 会话ID

    返回:
        LocalKernelClient 实例
    """
    return LocalKernelManager.get_client(conv_id)


if __name__ == "__main__":
    # 测试本地内核执行
    print("=" * 50)
    print("Local Jupyter Kernel Test")
    print("=" * 50)

    client = get_local_kernel_client("test_conv")

    print("\nTest 1: Simple calculation")
    result = client.execute("print(1 + 1)")
    print(f"Result: {result}")

    print("\nTest 2: Variable persistence")
    client.execute("x = 42")
    result = client.execute("print(x * 2)")
    print(f"Result: {result}")

    print("\nTest 3: Error handling")
    result = client.execute("print(undefined_variable)")
    print(f"Result: {result}")

    client.shutdown()
    print("\nTest completed!")
