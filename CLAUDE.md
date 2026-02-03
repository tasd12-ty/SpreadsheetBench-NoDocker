# CLAUDE.md - Project Instructions for Claude Code

## Project Overview

SpreadsheetBench-NoDocker is a benchmark for evaluating LLMs on real-world spreadsheet manipulation tasks. This is a modified fork that removes the Docker requirement, enabling local execution via Jupyter kernels.

**Key Features:**
- 912 real-world spreadsheet manipulation questions from Excel forums
- 2,729 test cases with OJ-style (Online Judge) evaluation
- Single-round and multi-round inference modes
- Local vLLM model deployment support
- ReAct (Reasoning + Acting) prompt techniques

## Tech Stack

- **Language:** Python 3.8+
- **Core Libraries:** pandas, openpyxl, openai, transformers, jupyter_client, vllm, tornado
- **Execution:** Local Jupyter kernels (no Docker required)
- **LLM Interface:** OpenAI-compatible API

## Project Structure

```
SpreadsheetBench-NoDocker/
├── data/                    # Benchmark datasets (tar.gz archives)
├── inference/               # Model inference code
│   ├── inference_single.py  # Single-round inference
│   ├── inference_multiple.py # Multi-round inference
│   ├── llm_api.py           # LLM API wrapper
│   ├── code_exec.py         # Code execution abstraction
│   ├── local_kernel.py      # Local Jupyter kernel client
│   ├── prompt_format.py     # Prompt templates
│   └── scripts/             # Shell scripts for inference
├── evaluation/              # Benchmark evaluation (Windows only)
├── code_exec_docker/        # Code execution backends
│   ├── api.py               # HTTP API server
│   └── jupyter.py           # Jupyter gateway implementations
└── scripts/                 # Setup and utility scripts
```

## Quick Start

```bash
# Setup environment
chmod +x scripts/setup_local.sh && ./scripts/setup_local.sh
source venv/bin/activate

# Extract dataset
cd data && tar -xzf sample_data_200.tar.gz && cd ..

# Start vLLM server (Terminal 1)
./scripts/start_vllm_server.sh --model Qwen/Qwen-7B-Chat --port 8000

# Run inference (Terminal 2)
export USE_LOCAL_KERNEL=1
./scripts/run_local_inference.sh --model Qwen/Qwen-7B-Chat --base_url http://localhost:8000/v1 --api_key dummy --mode single
```

## Environment Variables

```bash
USE_LOCAL_KERNEL=1   # Enable local Jupyter kernel execution (default)
USE_DOCKER=0         # Disable Docker backend
USE_KUBERNETES=0     # Disable Kubernetes backend
```

## Inference Modes

| Mode | Setting | Description |
|------|---------|-------------|
| single | - | Single-round, initial response only |
| multiple | row_exec | Multi-round with spreadsheet preview |
| multiple | react_exec | ReAct with exploration phase |
| multiple | row_react_exec | ReAct + spreadsheet preview |

## Key Development Conventions

### Code Execution Backend
- `code_exec.py` provides backend-agnostic execution interface
- Priority order: Kubernetes > Docker > Local (controlled via env vars)
- `local_kernel.py` uses singleton pattern for kernel management

### Model Name Handling
- Model names with slashes (e.g., `meta-llama/Llama-2-7b`) are converted to underscores for file paths
- Applied to output directories and file naming

### Output Locations
- Conversation results: `inference/outputs/conv_{setting}_{model}.jsonl`
- Error logs: `inference/log/{setting}_{model}.jsonl`
- Generated spreadsheets: `data/{dataset}/outputs/{setting}_{model}/`

### Prompt Templates
- `PROMPT_FORMAT_SINGLE`: Single-round basic prompt
- `PROMPT_DF_RCT_FORMAT`: ReAct with spreadsheet preview
- `PROMPT_NO_DF_RCT_FORMAT`: ReAct without spreadsheet preview

## Testing/Evaluation

**Note:** Evaluation requires Windows due to `win32com` library dependency.

Workflow:
1. Run inference on Linux/macOS
2. Transfer results to Windows machine
3. Run `evaluation/evaluation.py` to compare outputs

## Common Commands

```bash
# Single-round inference
python inference/inference_single.py --model MODEL --api_key KEY --base_url URL --dataset sample_data_200

# Multi-round inference with ReAct
python inference/inference_multiple.py --model MODEL --api_key KEY --base_url URL --dataset sample_data_200 --setting react_exec --max_turn_num 5

# Start local vLLM server
python -m vllm.entrypoints.openai.api_server --model MODEL --port 8000 --gpu-memory-utilization 0.85
```

## Important Files to Know

| File | Purpose |
|------|---------|
| `inference/code_exec.py` | Abstracts code execution across backends |
| `inference/local_kernel.py` | Local Jupyter kernel implementation |
| `inference/llm_api.py` | LLM API wrapper with retry logic |
| `inference/prompt_format.py` | All prompt templates |
| `code_exec_docker/api.py` | HTTP API server with multi-backend support |
| `code_exec_docker/jupyter.py` | Jupyter gateway implementations |

## Error Handling

- Execution results are parsed for error tracebacks
- Multi-part error collection from Jupyter output
- ANSI escape sequences are stripped for clean output
- Graceful fallback when code execution fails
