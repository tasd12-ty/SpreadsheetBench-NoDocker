# SpreadsheetBench - No Docker Version

This is a modified version of [SpreadsheetBench](https://github.com/RUCKBReasoning/SpreadsheetBench) that can run **without Docker** on a single Ubuntu server. It supports both local model deployment (via vLLM) and code execution using local Jupyter kernels.

## Features

- **No Docker Required**: Run everything locally without containerization
- **Local Model Deployment**: Use vLLM to deploy LLMs on your own GPU
- **Single Server Setup**: Both model inference and benchmark testing on one machine
- **Compatible API**: Maintains OpenAI-compatible API interface

## Quick Start

### 1. Prerequisites

- Ubuntu 18.04+ (or other Linux distributions)
- Python 3.8+
- NVIDIA GPU with CUDA support (for local model deployment)
- At least 16GB RAM (32GB+ recommended for larger models)

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/tasd12-ty/SpreadsheetBench-NoDocker.git
cd SpreadsheetBench-NoDocker

# Run setup script
chmod +x scripts/setup_local.sh
./scripts/setup_local.sh

# Activate virtual environment
source venv/bin/activate
```

### 3. Extract Data

```bash
# Extract sample data (200 examples)
cd data
tar -xzf sample_data_200.tar.gz

# Or extract full dataset (912 examples)
tar -xzf all_data_912.tar.gz
```

### 4. Start Local LLM Server (Option A: Using vLLM)

```bash
# Start vLLM server with your chosen model
chmod +x scripts/start_vllm_server.sh
./scripts/start_vllm_server.sh --model Qwen/Qwen-7B-Chat --port 8000

# For larger models with multiple GPUs:
./scripts/start_vllm_server.sh --model meta-llama/Llama-2-13b-chat-hf --port 8000 --tensor-parallel-size 2
```

### 5. Run Inference

```bash
# Enable local execution mode
export USE_LOCAL_KERNEL=1

# Run single-round inference
cd inference
python inference_single.py \
    --model Qwen/Qwen-7B-Chat \
    --base_url http://localhost:8000/v1 \
    --api_key dummy \
    --dataset sample_data_200 \
    --row 5

# Or use the convenience script
chmod +x scripts/run_local_inference.sh
./scripts/run_local_inference.sh \
    --model Qwen/Qwen-7B-Chat \
    --base_url http://localhost:8000/v1 \
    --api_key dummy \
    --mode single
```

### 6. Multi-Round Inference

```bash
export USE_LOCAL_KERNEL=1
cd inference

python inference_multiple.py \
    --model Qwen/Qwen-7B-Chat \
    --base_url http://localhost:8000/v1 \
    --api_key dummy \
    --dataset sample_data_200 \
    --setting row_exec \
    --max_turn_num 5 \
    --row 5
```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_LOCAL_KERNEL` | `0` | Set to `1` to use local Jupyter kernel instead of Docker |
| `USE_DOCKER` | `0` | Set to `1` to use Docker backend (original behavior) |
| `USE_KUBERNETES` | `0` | Set to `1` to use Kubernetes backend |

### Inference Arguments

| Argument | Description |
|----------|-------------|
| `--model` | Model name (e.g., Qwen/Qwen-7B-Chat) |
| `--base_url` | API endpoint (e.g., http://localhost:8000/v1) |
| `--api_key` | API key (use "dummy" for local vLLM) |
| `--dataset` | Dataset name (sample_data_200 or all_data_912) |
| `--row` | Number of rows to include in prompt (default: 5) |
| `--setting` | Multi-round setting: row_exec, react_exec, row_react_exec |
| `--max_turn_num` | Maximum conversation turns (default: 5) |

## Using External APIs

You can also use external API providers instead of local vLLM:

```bash
# Using OpenAI API
export USE_LOCAL_KERNEL=1
python inference_single.py \
    --model gpt-4 \
    --base_url https://api.openai.com/v1 \
    --api_key sk-your-api-key \
    --dataset sample_data_200

# Using other OpenAI-compatible APIs
python inference_single.py \
    --model your-model \
    --base_url https://your-api-endpoint/v1 \
    --api_key your-api-key \
    --dataset sample_data_200
```

## Directory Structure

```
SpreadsheetBench-NoDocker/
├── data/                       # Benchmark datasets
│   ├── sample_data_200.tar.gz
│   └── all_data_912.tar.gz
├── inference/                  # Inference scripts
│   ├── inference_single.py     # Single-round inference
│   ├── inference_multiple.py   # Multi-round inference
│   ├── local_kernel.py         # Local Jupyter kernel client
│   ├── code_exec.py            # Code execution utilities
│   └── llm_api.py              # LLM API interface
├── code_exec_docker/           # Code execution backend (optional Docker support)
├── evaluation/                 # Evaluation scripts
├── scripts/                    # Helper scripts
│   ├── setup_local.sh          # Setup script
│   ├── run_local_inference.sh  # Inference runner
│   └── start_vllm_server.sh    # vLLM server launcher
└── requirements.txt            # Python dependencies
```

## Troubleshooting

### Jupyter Kernel Issues

If you encounter kernel issues:

```bash
# Reinstall kernel
python -m ipykernel install --user --name python3
```

### CUDA/GPU Issues

```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Check GPU memory
nvidia-smi
```

### Memory Issues

For large models, adjust vLLM settings:

```bash
./scripts/start_vllm_server.sh \
    --model your-model \
    --gpu-memory-utilization 0.85 \
    --max-model-len 2048
```

## Evaluation

Note: The evaluation component requires Windows due to `win32com` dependency for Excel file inspection. You can:

1. Run inference on Linux, then transfer results to Windows for evaluation
2. Use a Windows VM or remote Windows machine for evaluation
3. Use Wine with win32com (experimental)

## Credits

- Original SpreadsheetBench: [RUCKBReasoning/SpreadsheetBench](https://github.com/RUCKBReasoning/SpreadsheetBench)
- vLLM: [vllm-project/vllm](https://github.com/vllm-project/vllm)

## License

CC BY SA 4.0 (following the original SpreadsheetBench license)
