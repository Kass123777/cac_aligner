#!/usr/bin/env python3
"""Generate Comprehensive Alignment Evaluation Report"""

import os
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def load_evaluation_results(results_dir: str) -> Dict[str, Any]:
    """加载评估结果"""
    results = {
        'safety': {},
        'utility': {}
    }
    
    results_path = Path(results_dir)
    
    # 加载安全性评估结果
    safety_summary = results_path / 'safety_evaluation_summary.json'
    if safety_summary.exists():
        with open(safety_summary, 'r', encoding='utf-8') as f:
            results['safety'] = json.load(f)
    
    # 加载有用性评估结果
    utility_summary = results_path / 'utility_evaluation_summary.json'
    if utility_summary.exists():
        with open(utility_summary, 'r', encoding='utf-8') as f:
            results['utility'] = json.load(f)
    
    return results

def generate_summary_table(results: Dict[str, Any]) -> pd.DataFrame:
    """生成汇总表格"""
    data = []
    
    # 获取所有实验的键
    all_keys = set()
    if results['safety']:
        all_keys.update(results['safety'].keys())
    if results['utility']:
        all_keys.update(results['utility'].keys())
    
    for key in all_keys:
        row = {'experiment': key}
        
        # 解析实验信息
        parts = key.split('_')
        if len(parts) >= 3:
            row['test_dataset'] = parts[0]
            row['base_model'] = '_'.join(parts[1:5:2])
            row['aligner_name'] = '_'.join(parts[-5:])
        
        # 安全性指标
        if key in results['safety']:
            safety_metrics = results['safety'][key]['metrics']
            row['safety_improvement_rate'] = safety_metrics.get('safety_improvement_rate', 0)
            row['safety_total_samples'] = safety_metrics.get('total_samples', 0)
            row['corrected_safer'] = safety_metrics.get('corrected_safer', 0)
            row['original_safer'] = safety_metrics.get('original_safer', 0)
            row['equal_safety'] = safety_metrics.get('equal_safety', 0)
        else:
            row['safety_improvement_rate'] = None
            row['safety_total_samples'] = None
            row['corrected_safer'] = None
            row['original_safer'] = None
            row['equal_safety'] = None
        
        # 有用性指标
        if key in results['utility']:
            utility_metrics = results['utility'][key]['metrics']
            row['utility_improvement_rate'] = utility_metrics.get('utility_improvement_rate', 0)
            row['utility_retention_rate'] = utility_metrics.get('utility_retention_rate', 0)
            row['utility_total_samples'] = utility_metrics.get('total_samples', 0)
            row['corrected_better'] = utility_metrics.get('corrected_better', 0)
            row['original_better'] = utility_metrics.get('original_better', 0)
            row['equal_utility'] = utility_metrics.get('equal_utility', 0)
        else:
            row['utility_improvement_rate'] = None
            row['utility_retention_rate'] = None
            row['utility_total_samples'] = None
            row['corrected_better'] = None
            row['original_better'] = None
            row['equal_utility'] = None
        
        data.append(row)
    
    return pd.DataFrame(data)

def create_visualization(df: pd.DataFrame, output_dir: str):
    """创建可视化图表"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # 1. 安全性改进率对比
    safety_data = df[df['safety_improvement_rate'].notna()]
    if not safety_data.empty:
        ax1 = axes[0, 0]
        bars1 = ax1.bar(range(len(safety_data)), safety_data['safety_improvement_rate'], 
                       color='lightcoral', alpha=0.7)
        ax1.set_title('Safety Improvement Rate Comparison', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Safety Improvement Rate', fontsize=12)
        ax1.set_xlabel('Experiments', fontsize=12)
        ax1.set_xticks(range(len(safety_data)))
        ax1.set_xticklabels(safety_data['experiment'], rotation=45, ha='right')
        ax1.grid(True, alpha=0.3)
        
        # 添加数值标签
        for i, bar in enumerate(bars1):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{height:.2%}', ha='center', va='bottom', fontsize=10)
    
    # 2. 有用性改进率对比
    utility_data = df[df['utility_improvement_rate'].notna()]
    if not utility_data.empty:
        ax2 = axes[0, 1]
        bars2 = ax2.bar(range(len(utility_data)), utility_data['utility_improvement_rate'], 
                       color='lightblue', alpha=0.7)
        ax2.set_title('Utility Improvement Rate Comparison', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Utility Improvement Rate', fontsize=12)
        ax2.set_xlabel('Experiments', fontsize=12)
        ax2.set_xticks(range(len(utility_data)))
        ax2.set_xticklabels(utility_data['experiment'], rotation=45, ha='right')
        ax2.grid(True, alpha=0.3)
        
        # 添加数值标签
        for i, bar in enumerate(bars2):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{height:.2%}', ha='center', va='bottom', fontsize=10)
    
    # 3. 安全性vs有用性散点图
    combined_data = df[(df['safety_improvement_rate'].notna()) & 
                      (df['utility_improvement_rate'].notna())]
    if not combined_data.empty:
        ax3 = axes[1, 0]
        scatter = ax3.scatter(combined_data['safety_improvement_rate'], 
                            combined_data['utility_improvement_rate'],
                            c=range(len(combined_data)), cmap='viridis', 
                            s=100, alpha=0.7)
        ax3.set_title('Safety vs Utility Improvement Rate', fontsize=14, fontweight='bold')
        ax3.set_xlabel('Safety Improvement Rate', fontsize=12)
        ax3.set_ylabel('Utility Improvement Rate', fontsize=12)
        ax3.grid(True, alpha=0.3)
        
        # 添加对角线
        ax3.plot([0, 1], [0, 1], 'k--', alpha=0.5, label='Ideal Line')
        ax3.legend()
        
        # 添加标签
        for i, row in combined_data.iterrows():
            ax3.annotate(row['experiment'], 
                        (row['safety_improvement_rate'], row['utility_improvement_rate']),
                        xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    # 4. 有用性保持率对比
    if not utility_data.empty:
        ax4 = axes[1, 1]
        bars4 = ax4.bar(range(len(utility_data)), utility_data['utility_retention_rate'], 
                       color='lightgreen', alpha=0.7)
        ax4.set_title('Utility Retention Rate Comparison', fontsize=14, fontweight='bold')
        ax4.set_ylabel('Utility Retention Rate', fontsize=12)
        ax4.set_xlabel('Experiments', fontsize=12)
        ax4.set_xticks(range(len(utility_data)))
        ax4.set_xticklabels(utility_data['experiment'], rotation=45, ha='right')
        ax4.grid(True, alpha=0.3)
        
        # 添加数值标签
        for i, bar in enumerate(bars4):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{height:.2%}', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/evaluation_charts.png', dpi=300, bbox_inches='tight')
    plt.close()

def generate_markdown_report(df: pd.DataFrame, results: Dict[str, Any], output_file: str):
    """生成Markdown格式报告"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# 伦理道德价值观对齐评估报告\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 执行摘要
        f.write("## 执行摘要\n\n")
        
        # 计算总体统计
        total_experiments = df['safety_total_samples'].sum()
        avg_safety_improvement = df['safety_improvement_rate'].mean() if df['safety_improvement_rate'].notna().any() else 0
        avg_utility_improvement = df['utility_improvement_rate'].mean() if df['utility_improvement_rate'].notna().any() else 0
        avg_utility_retention = df['utility_retention_rate'].mean() if df['utility_retention_rate'].notna().any() else 0
        
        f.write(f"- **总实验数量**: {total_experiments}\n")
        f.write(f"- **平均安全性改进率**: {avg_safety_improvement:.2%}\n")
        f.write(f"- **平均有用性改进率**: {avg_utility_improvement:.2%}\n")
        # f.write(f"- **平均有用性保持率**: {avg_utility_retention:.2%}\n\n")
        
        # 详细结果表格
        f.write("## 详细评估结果\n\n")
        f.write("### 汇总表格\n\n")
        
        # 创建表格
        f.write("| 实验 | 测试集 | 基础模型 | 对齐器 | 安全性改进率 | 有用性改进率 | 有用性保持率 |\n")
        f.write("|------|--------|----------|--------|--------------|--------------|---------------|\n")
        
        for _, row in df.iterrows():
            safety_rate = f"{row['safety_improvement_rate']:.2%}" if pd.notna(row['safety_improvement_rate']) else "N/A"
            utility_rate = f"{row['utility_improvement_rate']:.2%}" if pd.notna(row['utility_improvement_rate']) else "N/A"
            retention_rate = f"{row['utility_retention_rate']:.2%}" if pd.notna(row['utility_retention_rate']) else "N/A"
            
            f.write(f"| {row['experiment']} | {row.get('test_dataset', 'N/A')} | {row.get('base_model', 'N/A')} | {row.get('aligner_name', 'N/A')} | {safety_rate} | {utility_rate} | {retention_rate} |\n")
        
        f.write("\n")
        
        # 按测试集分组的结果
        f.write("### 测试集评估表现\n\n")
        
        grouped = df.groupby('test_dataset') if 'test_dataset' in df.columns else df.groupby('experiment')
        for dataset, group in grouped:
            f.write(f"#### {dataset}\n\n")
            
            avg_safety = group['safety_improvement_rate'].mean() if group['safety_improvement_rate'].notna().any() else 0
            avg_utility = group['utility_improvement_rate'].mean() if group['utility_improvement_rate'].notna().any() else 0
            avg_retention = group['utility_retention_rate'].mean() if group['utility_retention_rate'].notna().any() else 0
            
            f.write(f"- **样本数量**: {group['safety_total_samples'].sum()}\n")
            f.write(f"- **平均安全性改进率**: {avg_safety:.2%}\n")
            f.write(f"- **平均有用性改进率**: {avg_utility:.2%}\n")
            # f.write(f"- **平均有用性保持率**: {avg_retention:.2%}\n\n")
        
        # # 分析和建议
        # f.write("## 分析与建议\n\n")
        
        # f.write("### 主要发现\n\n")
        
        # # 找出表现最好的实验
        # if df['safety_improvement_rate'].notna().any():
        #     best_safety = df.loc[df['safety_improvement_rate'].idxmax()]
        #     f.write(f"- **最佳安全性改进**: {best_safety['experiment']} ({best_safety['safety_improvement_rate']:.2%})\n")
        
        # if df['utility_improvement_rate'].notna().any():
        #     best_utility = df.loc[df['utility_improvement_rate'].idxmax()]
        #     f.write(f"- **最佳有用性改进**: {best_utility['experiment']} ({best_utility['utility_improvement_rate']:.2%})\n")
        
        # if df['utility_retention_rate'].notna().any():
        #     best_retention = df.loc[df['utility_retention_rate'].idxmax()]
        #     f.write(f"- **最佳有用性保持**: {best_retention['experiment']} ({best_retention['utility_retention_rate']:.2%})\n")
        
        # f.write("\n### 建议\n\n")
        
        # if avg_safety_improvement > 0.1:
        #     f.write("- ✅ 安全性对齐效果良好，平均改进率超过0%\n")
        # else:
        #     f.write("- ⚠️ 安全性对齐效果有待提升，建议优化对齐策略\n")
        
        # if avg_utility_retention > 0.1:
        #     f.write("- ✅ 有用性保持良好，大部分情况下维持或提升了有用性\n")
        # else:
        #     f.write("- ⚠️ 有用性保持需要改进，存在能力退化风险\n")
        
        # f.write("\n---\n")
        # f.write("*本报告由 June Aligner 评估系统自动生成*\n")

def main():
    parser = argparse.ArgumentParser(description='Generate Alignment Evaluation Report')
    parser.add_argument('--results_dir', type=str, required=True, help='Directory containing evaluation results')
    # parser.add_argument('--output', type=str, default='alignment_report.md', help='Output report file')
    parser.add_argument('--output', type=str, default='./reports', help='Output directory')
    
    args = parser.parse_args()
    
    # 创建输出目录
    os.makedirs(args.output, exist_ok=True)
    
    # 加载评估结果
    print("加载评估结果...")
    results = load_evaluation_results(args.results_dir)
    
    if not results['safety'] and not results['utility']:
        print("未找到评估结果文件")
        return
    
    # 生成汇总表格
    print("生成汇总表格...")
    df = generate_summary_table(results)
    
    # 保存CSV文件
    csv_file = f"{args.output}/evaluation_summary.csv"
    df.to_csv(csv_file, index=False, encoding='utf-8')
    print(f"汇总表格已保存到: {csv_file}")
    
    # 创建可视化图表
    # print("创建可视化图表...")
    # try:
    #     create_visualization(df, args.output_dir)
    #     print(f"可视化图表已保存到: {args.output_dir}/evaluation_charts.png")
    # except Exception as e:
    #     print(f"创建图表时出错: {e}")
    
    # 生成Markdown报告
    print("生成报告...")
    report_file = f"{args.output}/alignment_report.md"
    generate_markdown_report(df, results, report_file)
    print(f"报告已保存到: {report_file}")
    
    # 打印摘要
    print("\n=== 评估摘要 ===")
    print(f"总实验数量: {len(df)}")
    if df['safety_improvement_rate'].notna().any():
        print(f"平均安全性改进率: {df['safety_improvement_rate'].mean():.2%}")
    if df['utility_improvement_rate'].notna().any():
        print(f"平均有用性改进率: {df['utility_improvement_rate'].mean():.2%}")
    # if df['utility_retention_rate'].notna().any():
    #     print(f"平均有用性保持率: {df['utility_retention_rate'].mean():.2%}")

if __name__ == '__main__':
    main() 