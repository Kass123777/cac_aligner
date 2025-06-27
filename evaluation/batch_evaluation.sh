#!/bin/bash

# June Aligner 批量评估脚本
# 使用方法: ./batch_evaluation.sh

set -e

# =============================================================================
# 配置参数
# =============================================================================

# API配置 - 已更新为用户指定的配置
API_KEY="sk-ZA45vUH6dDT89S5XwYpwLbL6JtD4cdZrhqtaEJrIBcX7ffFn"
API_BASE="https://api3.xhub.chat/v1/chat/completions"
EVAL_MODEL="gpt-4o"

# 实验配置
TEST_DATASET="beavertails"           # 测试数据集: beavertails, harmfulqa
BASE_MODEL="llama_sft_70b_slice_2167"  # 基础模型名称
ALIGNER_NAME="lora_aligner_sft_r4_epoch3"  # 对齐器名称

# 输出配置
OUTPUT_DIR="./eval_results_$(date +%Y%m%d_%H%M%S)"
INFERENCE_RESULTS_DIR="/aifs4su/yaodong/boyuan/june_aligner/inference_results"

# =============================================================================
# 参数验证
# =============================================================================

echo "==============================================="
echo "June Aligner 批量评估系统"
echo "==============================================="
echo "API模型: $EVAL_MODEL"
echo "API地址: $API_BASE"
echo "测试数据集: $TEST_DATASET"
echo "基础模型: $BASE_MODEL"
echo "对齐器: $ALIGNER_NAME"
echo "输出目录: $OUTPUT_DIR"
echo "==============================================="

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# =============================================================================
# 单个实验评估
# =============================================================================

echo "🔍 开始单个实验评估..."

# 1. 安全性评估
echo "📊 执行安全性评估..."
python3 ethics_evaluate.py \
    --api_key "$API_KEY" \
    --api_base "$API_BASE" \
    --eval_model "$EVAL_MODEL" \
    --test_dataset "$TEST_DATASET" \
    --base_model "$BASE_MODEL" \
    --aligner_name "$ALIGNER_NAME" \
    --inference_results_dir "$INFERENCE_RESULTS_DIR" \
    --output_dir "$OUTPUT_DIR"

if [ $? -eq 0 ]; then
    echo "✅ 安全性评估完成"
else
    echo "❌ 安全性评估失败"
    exit 1
fi

# 2. 有用性评估  
echo "📊 执行有用性评估..."
python3 general_benchmark.py \
    --api_key "$API_KEY" \
    --api_base "$API_BASE" \
    --eval_model "$EVAL_MODEL" \
    --test_dataset "$TEST_DATASET" \
    --base_model "$BASE_MODEL" \
    --aligner_name "$ALIGNER_NAME" \
    --inference_results_dir "$INFERENCE_RESULTS_DIR" \
    --output_dir "$OUTPUT_DIR"

if [ $? -eq 0 ]; then
    echo "✅ 有用性评估完成"
else
    echo "❌ 有用性评估失败"
    exit 1
fi

# 3. 生成报告
echo "📋 生成评估报告..."
python3 generate_report.py \
    --results_dir "$OUTPUT_DIR" \
    --output_dir "$OUTPUT_DIR/reports" \
    --output "alignment_report_${TEST_DATASET}_${BASE_MODEL}_${ALIGNER_NAME}.md"

if [ $? -eq 0 ]; then
    echo "✅ 报告生成完成"
else
    echo "❌ 报告生成失败"
    exit 1
fi

echo ""
echo "🎉 单个实验评估完成！"
echo "📁 结果保存在: $OUTPUT_DIR"
echo ""

# =============================================================================
# 批量评估示例
# =============================================================================

echo "🔍 开始批量评估示例..."

# 定义多个实验配置
declare -a EXPERIMENTS=(
    "beavertails:llama_sft_70b_slice_2167:lora_aligner_sft_r4_epoch3"
    "harmfulqa:llama_sft_70b_slice_2167:lora_aligner_sft_r4_epoch3"
    # 添加更多实验配置...
)

BATCH_OUTPUT_DIR="./batch_eval_results_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BATCH_OUTPUT_DIR"

for experiment in "${EXPERIMENTS[@]}"; do
    IFS=':' read -r dataset model aligner <<< "$experiment"
    
    echo ""
    echo "📊 评估实验: $dataset | $model | $aligner"
    
    # 安全性评估
    python3 ethics_evaluate.py \
        --api_key "$API_KEY" \
        --api_base "$API_BASE" \
        --eval_model "$EVAL_MODEL" \
        --test_dataset "$dataset" \
        --base_model "$model" \
        --aligner_name "$aligner" \
        --inference_results_dir "$INFERENCE_RESULTS_DIR" \
        --output_dir "$BATCH_OUTPUT_DIR"
    
    # 有用性评估
    python3 general_benchmark.py \
        --api_key "$API_KEY" \
        --api_base "$API_BASE" \
        --eval_model "$EVAL_MODEL" \
        --test_dataset "$dataset" \
        --base_model "$model" \
        --aligner_name "$aligner" \
        --inference_results_dir "$INFERENCE_RESULTS_DIR" \
        --output_dir "$BATCH_OUTPUT_DIR"
    
    echo "✅ 实验 $experiment 完成"
done

# 生成批量报告
echo "📋 生成批量评估报告..."
python3 generate_report.py \
    --results_dir "$BATCH_OUTPUT_DIR" \
    --output_dir "$BATCH_OUTPUT_DIR/reports" \
    --output "batch_alignment_report_$(date +%Y%m%d).md"

echo ""
echo "🎉 批量评估完成！"
echo "📁 结果保存在: $BATCH_OUTPUT_DIR"

# =============================================================================
# 自动发现模式示例
# =============================================================================

echo ""
echo "🔍 自动发现模式示例..."

AUTO_OUTPUT_DIR="./auto_eval_results_$(date +%Y%m%d_%H%M%S)"

echo "📊 使用自动发现模式评估所有实验..."

# 安全性评估 - 自动发现
python3 ethics_evaluate.py \
    --api_key "$API_KEY" \
    --api_base "$API_BASE" \
    --eval_model "$EVAL_MODEL" \
    --auto_discover \
    --inference_results_dir "$INFERENCE_RESULTS_DIR" \
    --output_dir "$AUTO_OUTPUT_DIR"

# 有用性评估 - 自动发现
python3 general_benchmark.py \
    --api_key "$API_KEY" \
    --api_base "$API_BASE" \
    --eval_model "$EVAL_MODEL" \
    --auto_discover \
    --inference_results_dir "$INFERENCE_RESULTS_DIR" \
    --output_dir "$AUTO_OUTPUT_DIR"

# 生成报告
python3 generate_report.py \
    --results_dir "$AUTO_OUTPUT_DIR" \
    --output_dir "$AUTO_OUTPUT_DIR/reports" \
    --output "auto_discovery_report_$(date +%Y%m%d).md"

echo "🎉 自动发现评估完成！"
echo "📁 结果保存在: $AUTO_OUTPUT_DIR"

echo ""
echo "==============================================="
echo "🎊 所有评估任务完成！"
echo "==============================================="
echo "📊 单个实验结果: $OUTPUT_DIR"
echo "📊 批量评估结果: $BATCH_OUTPUT_DIR"  
echo "📊 自动发现结果: $AUTO_OUTPUT_DIR"
echo "===============================================" 