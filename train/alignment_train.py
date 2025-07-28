#!/usr/bin/env python3
"""
对齐训练脚本
执行LLaMA-Factory的LoRA微调训练
"""

import os
import subprocess
import sys
import argparse
from pathlib import Path


def parse_arguments():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(
        description="对齐训练脚本 - 执行LLaMA-Factory的LoRA微调训练",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--base_model",
        type=str,
        default="./models/base_model/",
        help="基础模型路径"
    )

    parser.add_argument(
        "--train_data",
        type=str,
        default="./data/alignment_train/",
        help="训练数据路径"
    )

    parser.add_argument(
        "--output_dir",
        type=str,
        default="./models/aligned_model/",
        help="输出模型保存路径"
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="训练轮次"
    )

    parser.add_argument(
        "--batch_size",
        type=int,
        default=16,
        help="批次大小"
    )

    return parser.parse_args()


def run_alignment_training(args):
    """
    执行对齐训练的主函数
    """
    try:
        # 获取项目根目录(该文件目录的上一级)
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        llama_factory_dir = os.path.join(root_dir, "LLaMA-Factory")

        # 切换到LLaMA-Factory目录
        os.chdir(llama_factory_dir)

        # 检查配置文件是否存在
        config_file = "examples/train_lora/gemma3_lora_sft.yaml"
        if not os.path.exists(config_file):
            print(f"错误：配置文件不存在: {config_file}")
            return False

        # 执行训练命令
        cmd = ["llamafactory-cli", "train", config_file]

        # 运行命令并实时输出
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )

        # 实时打印输出
        for line in process.stdout:
            print(line.rstrip())

        # 等待进程完成
        return_code = process.wait()

        if return_code == 0:
            print("训练完成！")
            return True
        else:
            print(f"训练失败，返回码: {return_code}")
            return False

    except FileNotFoundError as e:
        print(f"命令未找到: {e}")
        print("请确保已安装LLaMA-Factory并且llamafactory-cli在PATH中")
        return False
    except Exception as e:
        print(f"执行过程中发生错误: {e}")
        return False


def main():
    """
    主函数
    """
    # 解析命令行参数
    args = parse_arguments()

    print("开始执行对齐训练...")
    print("=" * 50)

    success = run_alignment_training(args)

    print("=" * 50)
    if success:
        print("训练任务成功完成！")
        sys.exit(0)
    else:
        print("训练任务失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()
