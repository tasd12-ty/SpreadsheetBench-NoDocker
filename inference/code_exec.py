"""
代码执行模块 - 支持本地和远程两种执行模式
Code execution module - supports both local and remote execution modes
"""
import os

# 检查是否启用本地执行模式
# 设置环境变量 USE_LOCAL_KERNEL=1 可启用本地模式，无需 Docker
USE_LOCAL_KERNEL = os.environ.get("USE_LOCAL_KERNEL", "0").lower() == "1"

if USE_LOCAL_KERNEL:
    from local_kernel import get_local_kernel_client
else:
    from jupyter_kernel_cli import ClientJupyterKernel


def get_exec_client(url, conv_id):
    """
    根据配置获取代码执行客户端

    参数:
        url: 远程执行服务的 URL（本地模式下忽略）
        conv_id: 会话ID

    返回:
        执行客户端实例

    说明:
        - USE_LOCAL_KERNEL=1: 使用本地 Jupyter 内核，无需 Docker
        - USE_LOCAL_KERNEL=0: 使用 HTTP 客户端连接 Docker 执行服务
    """
    if USE_LOCAL_KERNEL:
        # 本地模式：直接使用本地 Jupyter 内核
        client = get_local_kernel_client(conv_id)
        print(f"Using local kernel for execution (conv_id={conv_id})")
    else:
        # 远程模式：通过 HTTP API 连接 Docker 执行服务
        client = ClientJupyterKernel(url, conv_id)
    return client

def extract_code(response):
    if response.find('```python') != -1:
        code = response[response.find('```python') + len('```python'):]
        code = code[:code.find('```')].lstrip('\n').rstrip('\n')
    else:
        code = response
    return code

def exec_code(client, code):
    res = client.execute(code)
    if res.find('-----') != -1:
        tracebacks = res.split('\n\n\n\n')
        error_feedback = ''
        for t in tracebacks:
            if t.find('Error') != -1:
                error_feedback += t + '\n'
                break
        for t in tracebacks:
            if len(t) >= len('Cell') and t[:len('Cell')] == 'Cell':
                error_feedback += t
                break
        error_feedback += tracebacks[-1]
        return error_feedback
    else:
        return res
