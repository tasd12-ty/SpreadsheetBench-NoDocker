import os

# Check if local execution mode is enabled
USE_LOCAL_KERNEL = os.environ.get("USE_LOCAL_KERNEL", "0").lower() == "1"

if USE_LOCAL_KERNEL:
    from local_kernel import get_local_kernel_client
else:
    from jupyter_kernel_cli import ClientJupyterKernel


def get_exec_client(url, conv_id):
    """
    Get execution client based on configuration.

    If USE_LOCAL_KERNEL=1, uses local Jupyter kernel (no Docker required).
    Otherwise, uses HTTP client to communicate with Docker-based execution service.
    """
    if USE_LOCAL_KERNEL:
        client = get_local_kernel_client(conv_id)
        print(f"Using local kernel for execution (conv_id={conv_id})")
    else:
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
