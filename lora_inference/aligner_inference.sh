#!/bin/bash

# Aligner Inference Shell Script
# 用法: ./aligner_inference.sh <aligner_name> <output_dir> <test_file1> [test_file2] [test_file3] ...

# 检查参数数量
if [ $# -lt 3 ]; then
    echo "用法: $0 <aligner_name> <output_dir> <test_file1> [test_file2] [test_file3] ..."
    echo ""
    echo "参数说明:"
    echo "  aligner_name  : 对齐器模型名称 (例如: lora_aligner_sft_r4_epoch3)"
    echo "  output_dir    : 输出目录路径"
    echo "  test_file(s)  : 测试文件路径 (可以传递多个文件)"
    echo ""
    echo "示例:"
    echo "  $0 lora_aligner_sft_r4_epoch3 /path/to/output /path/to/test1.json /path/to/test2.json"
    exit 1
fi

# 获取参数
ALIGNER_NAME=$1
OUTPUT_DIR=$2
shift 2  # 移除前两个参数，剩下的都是测试文件

# 构建测试文件列表
TEST_FILES=("$@")

# 检查测试文件是否存在
for test_file in "${TEST_FILES[@]}"; do
    if [ ! -f "$test_file" ]; then
        echo "错误: 测试文件不存在: $test_file"
        exit 1
    fi
done

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"




# 打印执行信息
echo "==================== Aligner Inference ===================="
echo "对齐器名称: $ALIGNER_NAME"
echo "输出目录: $OUTPUT_DIR"
echo "测试文件数量: ${#TEST_FILES[@]}"
for i in "${!TEST_FILES[@]}"; do
    echo "  文件 $((i+1)): ${TEST_FILES[i]}"
done
echo "=============================================================="

# 执行 Python 脚本
python3 "$SCRIPT_DIR/aligner_inference.py" \
    --aligner_name "$ALIGNER_NAME" \
    --file_path "$OUTPUT_DIR" \
    --test_file_list "${TEST_FILES[@]}"

# 检查执行结果
if [ $? -eq 0 ]; then
    echo "✅ Aligner inference 执行成功!"
else
    echo "❌ Aligner inference 执行失败!"
    exit 1
fi 