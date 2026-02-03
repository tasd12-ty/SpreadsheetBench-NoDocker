# SpreadsheetBench 无 Docker 版本 - 代码改动说明

本文档详细说明了为实现无 Docker 运行所做的所有代码改动。

## 改动概览

| 文件路径 | 改动类型 | 说明 |
|---------|---------|------|
| `code_exec_docker/jupyter.py` | 修改 | 添加本地 Jupyter Gateway 支持 |
| `code_exec_docker/api.py` | 修改 | 支持多后端切换 |
| `inference/local_kernel.py` | 新增 | 本地 Jupyter 内核客户端 |
| `inference/code_exec.py` | 修改 | 支持本地/远程执行切换 |
| `inference/inference_single.py` | 修改 | 支持本地路径解析 |
| `inference/inference_multiple.py` | 修改 | 支持本地路径解析 |
| `requirements.txt` | 修改 | 添加本地执行依赖 |
| `scripts/setup_local.sh` | 新增 | 环境安装脚本 |
| `scripts/run_local_inference.sh` | 新增 | 推理运行脚本 |
| `scripts/start_vllm_server.sh` | 新增 | vLLM 服务启动脚本 |
| `README_LOCAL.md` | 新增 | 英文使用说明 |

---

## 详细改动说明

### 1. `code_exec_docker/jupyter.py`

**改动内容：**

1. **条件导入 Docker 模块**
   - 原代码强制导入 `docker` 模块
   - 现在通过环境变量 `USE_DOCKER` 控制是否导入
   - Docker 不再是必需依赖

2. **新增 `JupyterGatewayLocal` 类**
   ```python
   class JupyterGatewayLocal:
       """
       本地 Jupyter Kernel Gateway - 无需 Docker 运行
       需要本地安装 jupyter_kernel_gateway
       """
   ```
   - 使用 `subprocess` 启动本地 Jupyter Kernel Gateway
   - 自动分配可用端口
   - 支持优雅关闭

3. **配置文件加载优化**
   - 添加配置文件存在性检查
   - 提供默认配置值

**关键代码：**
```python
# 环境变量控制后端选择
USE_DOCKER = os.environ.get("USE_DOCKER", "0").lower() == "1"
USE_KUBERNETES = os.environ.get("USE_KUBERNETES", "0").lower() == "1"

# 本地模式：启动 Jupyter Kernel Gateway 子进程
cmd = [
    "jupyter", "kernelgateway",
    "--KernelGatewayApp.ip=0.0.0.0",
    f"--KernelGatewayApp.port={self.port}",
]
```

---

### 2. `code_exec_docker/api.py`

**改动内容：**

1. **多后端支持**
   - 原代码仅支持 Docker 和 Kubernetes
   - 现在默认使用本地模式（无 Docker）

2. **后端选择逻辑**
   ```python
   if USE_KUBERNETES:
       JupyterKernelWrapper = JupyterGatewayKubernetes
   elif USE_DOCKER:
       JupyterKernelWrapper = JupyterGatewayDocker
   else:
       JupyterKernelWrapper = JupyterGatewayLocal  # 默认本地模式
   ```

---

### 3. `inference/local_kernel.py` (新增文件)

**功能说明：**

这是一个全新的模块，提供直接的本地 Jupyter 内核执行能力，完全绑过 HTTP API。

**核心类：**

1. **`LocalJupyterKernel`**
   - 直接使用 `jupyter_client` 与本地内核通信
   - 支持代码执行、输出收集、错误处理
   - 自动清理 ANSI 转义序列

2. **`LocalKernelClient`**
   - 与 `ClientJupyterKernel` 接口兼容
   - 可无缝替换原有的远程客户端

3. **`LocalKernelManager`**
   - 单例模式管理多个内核
   - 每个会话对应一个独立内核

**使用示例：**
```python
from local_kernel import get_local_kernel_client

client = get_local_kernel_client("my_session")
result = client.execute("print('Hello, World!')")
print(result)  # 输出: Hello, World!
```

---

### 4. `inference/code_exec.py`

**改动内容：**

1. **添加执行模式切换**
   ```python
   USE_LOCAL_KERNEL = os.environ.get("USE_LOCAL_KERNEL", "0").lower() == "1"

   def get_exec_client(url, conv_id):
       if USE_LOCAL_KERNEL:
           # 使用本地内核，无需网络请求
           client = get_local_kernel_client(conv_id)
       else:
           # 使用远程 HTTP API（原有行为）
           client = ClientJupyterKernel(url, conv_id)
       return client
   ```

---

### 5. `inference/inference_single.py`

**改动内容：**

1. **路径处理优化**
   - 本地模式使用绝对路径
   - Docker 模式使用 `/mnt/data` 挂载路径

   ```python
   if USE_LOCAL_KERNEL:
       # 本地模式：使用实际文件路径
       input_path = f"{dataset_path}/{data['spreadsheet_path']}/{file_name}"
       output_path = f"{output_file_path}/{file_name.rstrip('_input.xlsx')}_output.xlsx"
   else:
       # Docker 模式：使用容器内挂载路径
       input_path = f"/mnt/data/{data['spreadsheet_path']}/{file_name}"
       output_path = f"/mnt/data/outputs/single_{opt.model}/..."
   ```

---

### 6. `inference/inference_multiple.py`

**改动内容：**

与 `inference_single.py` 类似，添加了本地路径支持：
- 检测 `USE_LOCAL_KERNEL` 环境变量
- 根据执行模式选择正确的文件路径

---

### 7. `requirements.txt`

**改动内容：**

```diff
+ # Jupyter 本地执行依赖
+ jupyter_client>=8.0.0
+ jupyter_kernel_gateway>=3.0.0
+ ipykernel>=6.0.0

- docker==7.1.0
+ # 可选: Docker 支持 (仅在 USE_DOCKER=1 时需要)
+ # docker==7.1.0

+ # Tornado 用于 API 服务器
+ tornado>=6.0.0
+ requests>=2.25.0
```

---

### 8. `scripts/setup_local.sh` (新增文件)

**功能：** 一键安装本地运行环境

**主要步骤：**
1. 检查 Python 版本 (需要 3.8+)
2. 创建虚拟环境
3. 安装依赖包
4. 安装 Jupyter 内核
5. 创建必要目录

---

### 9. `scripts/run_local_inference.sh` (新增文件)

**功能：** 便捷运行推理任务

**支持参数：**
- `--model`: 模型名称
- `--base_url`: API 地址
- `--api_key`: API 密钥
- `--dataset`: 数据集名称
- `--mode`: 单轮/多轮模式
- `--setting`: 多轮设置

---

### 10. `scripts/start_vllm_server.sh` (新增文件)

**功能：** 启动本地 vLLM 模型服务

**支持参数：**
- `--model`: 模型路径或名称
- `--port`: 服务端口
- `--gpu-memory-utilization`: GPU 显存使用率
- `--tensor-parallel-size`: 张量并行数量

---

## 环境变量说明

| 变量名 | 默认值 | 说明 |
|-------|-------|------|
| `USE_LOCAL_KERNEL` | `0` | 设为 `1` 使用本地 Jupyter 内核 |
| `USE_DOCKER` | `0` | 设为 `1` 使用 Docker 后端 |
| `USE_KUBERNETES` | `0` | 设为 `1` 使用 Kubernetes 后端 |

**优先级：** Kubernetes > Docker > 本地模式

---

## 快速开始

```bash
# 1. 安装环境
./scripts/setup_local.sh
source venv/bin/activate

# 2. 解压数据
cd data && tar -xzf sample_data_200.tar.gz && cd ..

# 3. 启动本地模型服务 (可选，也可使用外部 API)
./scripts/start_vllm_server.sh --model Qwen/Qwen-7B-Chat

# 4. 运行推理
export USE_LOCAL_KERNEL=1
cd inference
python inference_single.py \
    --model Qwen/Qwen-7B-Chat \
    --base_url http://localhost:8000/v1 \
    --api_key dummy \
    --dataset sample_data_200
```

---

## 兼容性说明

- 所有改动保持向后兼容
- 设置 `USE_DOCKER=1` 可恢复原有 Docker 行为
- API 接口保持不变
