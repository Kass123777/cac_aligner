#!/bin/bash


# 设置实验参数
TEST_DATASET="beavertails"
BASE_MODEL="llama_sft_70b_slice_2167"
ALIGNER_NAME="lora_aligner_sft_r4_epoch3"
OUTPUT_DIR="./eval_results"

echo "开始评估: $TEST_DATASET | $BASE_MODEL | $ALIGNER_NAME"

# 1. 安全性评估
echo "执行安全性评估..."
python3 ethics_evaluate.py \
    --test_data "$TEST_DATASET" \
    --baseline "$BASE_MODEL" \
    --model_path "$ALIGNER_NAME" \

# 2. 有用性评估
echo "执行有用性评估..."
python3 general_benchmark.py \
    --test_data "$TEST_DATASET" \
    --baseline "$BASE_MODEL" \
    --model_path "$ALIGNER_NAME" \

# 3. 生成报告
echo "生成报告..."
python3 generate_report.py \
    --results_dir "$OUTPUT_DIR" \
    --output "$OUTPUT_DIR/reports"

echo "评估完成！结果保存在 $OUTPUT_DIR" 