#!/bin/bash
# Start vLLM server for local model deployment
# Usage: ./start_vllm_server.sh --model MODEL_PATH [--port PORT] [--gpu-memory-utilization UTILIZATION]

set -e

# Default values
MODEL=""
PORT=8000
GPU_MEMORY=0.9
TENSOR_PARALLEL=1
MAX_MODEL_LEN=4096

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --model)
            MODEL="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --gpu-memory-utilization)
            GPU_MEMORY="$2"
            shift 2
            ;;
        --tensor-parallel-size)
            TENSOR_PARALLEL="$2"
            shift 2
            ;;
        --max-model-len)
            MAX_MODEL_LEN="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate required arguments
if [ -z "$MODEL" ]; then
    echo "Error: --model is required"
    echo "Usage: ./start_vllm_server.sh --model MODEL_PATH [--port PORT]"
    echo ""
    echo "Example models:"
    echo "  - meta-llama/Llama-2-7b-chat-hf"
    echo "  - Qwen/Qwen-7B-Chat"
    echo "  - mistralai/Mistral-7B-Instruct-v0.2"
    echo "  - deepseek-ai/deepseek-coder-6.7b-instruct"
    exit 1
fi

echo "========================================"
echo "Starting vLLM Server"
echo "========================================"
echo "Model: $MODEL"
echo "Port: $PORT"
echo "GPU Memory Utilization: $GPU_MEMORY"
echo "Tensor Parallel Size: $TENSOR_PARALLEL"
echo "Max Model Length: $MAX_MODEL_LEN"
echo "========================================"

# Check if vLLM is installed
if ! python -c "import vllm" 2>/dev/null; then
    echo "vLLM not installed. Installing..."
    pip install vllm
fi

# Start vLLM server
python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL" \
    --port "$PORT" \
    --gpu-memory-utilization "$GPU_MEMORY" \
    --tensor-parallel-size "$TENSOR_PARALLEL" \
    --max-model-len "$MAX_MODEL_LEN" \
    --trust-remote-code

echo "========================================"
echo "vLLM Server stopped"
echo "========================================"
