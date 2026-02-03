#!/bin/bash
# Run inference locally without Docker
# Usage: ./run_local_inference.sh --model MODEL_NAME --base_url BASE_URL --api_key API_KEY [other options]

set -e

# Enable local kernel mode
export USE_LOCAL_KERNEL=1

# Default values
MODEL=""
BASE_URL="http://localhost:8000/v1"
API_KEY=""
DATASET="sample_data_200"
ROW=5
MODE="single"  # single or multiple
SETTING="row_exec"  # for multiple mode: row_exec, react_exec, row_react_exec
MAX_TURN=5

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --model)
            MODEL="$2"
            shift 2
            ;;
        --base_url)
            BASE_URL="$2"
            shift 2
            ;;
        --api_key)
            API_KEY="$2"
            shift 2
            ;;
        --dataset)
            DATASET="$2"
            shift 2
            ;;
        --row)
            ROW="$2"
            shift 2
            ;;
        --mode)
            MODE="$2"
            shift 2
            ;;
        --setting)
            SETTING="$2"
            shift 2
            ;;
        --max_turn)
            MAX_TURN="$2"
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
    echo "Usage: ./run_local_inference.sh --model MODEL_NAME --base_url BASE_URL --api_key API_KEY"
    exit 1
fi

# Navigate to inference directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../inference"

echo "========================================"
echo "Running SpreadsheetBench Inference"
echo "========================================"
echo "Mode: $MODE"
echo "Model: $MODEL"
echo "Base URL: $BASE_URL"
echo "Dataset: $DATASET"
echo "Local Kernel: Enabled"
echo "========================================"

if [ "$MODE" == "single" ]; then
    python inference_single.py \
        --model "$MODEL" \
        --base_url "$BASE_URL" \
        --api_key "$API_KEY" \
        --dataset "$DATASET" \
        --row "$ROW"
elif [ "$MODE" == "multiple" ]; then
    python inference_multiple.py \
        --model "$MODEL" \
        --base_url "$BASE_URL" \
        --api_key "$API_KEY" \
        --dataset "$DATASET" \
        --row "$ROW" \
        --setting "$SETTING" \
        --max_turn_num "$MAX_TURN"
else
    echo "Error: Invalid mode. Use 'single' or 'multiple'"
    exit 1
fi

echo "========================================"
echo "Inference completed!"
echo "========================================"
