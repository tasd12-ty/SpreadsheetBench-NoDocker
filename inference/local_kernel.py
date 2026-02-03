"""
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
    Direct local Jupyter kernel execution without Docker or HTTP API
    """

    def __init__(self, conv_id: str, kernel_name: str = "python3"):
        if not JUPYTER_CLIENT_AVAILABLE:
            raise ImportError("jupyter_client package is required for local execution. "
                              "Install it with: pip install jupyter_client ipykernel")

        self.conv_id = conv_id
        self.kernel_name = kernel_name
        self.km = None
        self.kc = None
        self._initialized = False
        self._start_kernel()
        atexit.register(self.shutdown)

    def _start_kernel(self):
        """Start a new Jupyter kernel."""
        self.km = jupyter_client.KernelManager(kernel_name=self.kernel_name)
        self.km.start_kernel()
        self.kc = self.km.client()
        self.kc.start_channels()
        self.kc.wait_for_ready(timeout=60)
        logging.info(f"Local Jupyter kernel started for conversation {self.conv_id}")

    def execute(self, code: str, timeout: int = 60) -> str:
        """
        Execute code in the kernel and return the result.

        Args:
            code: Python code to execute
            timeout: Execution timeout in seconds

        Returns:
            Execution result as string
        """
        if not self.kc:
            self._start_kernel()

        # Send execute request
        msg_id = self.kc.execute(code)

        outputs = []
        execution_done = False

        while not execution_done:
            try:
                # Get messages from iopub channel
                msg = self.kc.get_iopub_msg(timeout=timeout)
                msg_type = msg['msg_type']
                content = msg['content']

                if msg['parent_header'].get('msg_id') != msg_id:
                    continue

                if msg_type == 'error':
                    # Collect error traceback
                    traceback = '\n\n\n\n'.join(content.get('traceback', []))
                    outputs.append(self._strip_ansi(traceback))
                    execution_done = True

                elif msg_type == 'stream':
                    outputs.append(content.get('text', ''))

                elif msg_type in ['execute_result', 'display_data']:
                    data = content.get('data', {})
                    if 'text/plain' in data:
                        outputs.append(data['text/plain'])
                    if 'image/png' in data:
                        outputs.append(f"![image](data:image/png;base64,{data['image/png']})")

                elif msg_type == 'status':
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
        """Remove ANSI escape sequences from text."""
        import re
        pattern = re.compile(r'\x1B\[\d+(;\d+){0,2}m')
        return pattern.sub('', text)

    def shutdown(self):
        """Shutdown the kernel."""
        if self.kc:
            self.kc.stop_channels()
            self.kc = None
        if self.km:
            self.km.shutdown_kernel(now=True)
            self.km = None
        logging.info(f"Local kernel shutdown for conversation {self.conv_id}")


class LocalKernelClient:
    """
    Client interface compatible with ClientJupyterKernel for seamless switching
    """

    def __init__(self, conv_id: str):
        self.conv_id = conv_id
        self.kernel = None
        self._new_kernel = True
        print(f"LocalKernelClient initialized with conv_id={conv_id}")

    def execute(self, code: str) -> str:
        """Execute code and return result."""
        if self.kernel is None:
            self.kernel = LocalJupyterKernel(self.conv_id)
            self._new_kernel = True
        else:
            self._new_kernel = False

        result = self.kernel.execute(code)
        return result

    def shutdown(self):
        """Shutdown the kernel."""
        if self.kernel:
            self.kernel.shutdown()
            self.kernel = None


class LocalKernelManager:
    """
    Manager for multiple local kernels (one per conversation)
    """

    _instance = None
    _kernels: Dict[str, LocalKernelClient] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._kernels = {}
        return cls._instance

    @classmethod
    def get_client(cls, conv_id: str) -> LocalKernelClient:
        """Get or create a kernel client for the given conversation."""
        if conv_id not in cls._kernels:
            cls._kernels[conv_id] = LocalKernelClient(conv_id)
        return cls._kernels[conv_id]

    @classmethod
    def shutdown_all(cls):
        """Shutdown all kernels."""
        for conv_id, client in cls._kernels.items():
            client.shutdown()
        cls._kernels.clear()
        logging.info("All local kernels shutdown")


# Convenience function for direct usage
def get_local_kernel_client(conv_id: str) -> LocalKernelClient:
    """Get a local kernel client for direct code execution."""
    return LocalKernelManager.get_client(conv_id)


if __name__ == "__main__":
    # Test local kernel execution
    client = get_local_kernel_client("test_conv")

    print("Test 1: Simple calculation")
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
