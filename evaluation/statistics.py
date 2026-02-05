#!/usr/bin/env python3
"""
统计评估结果脚本
从评估JSON文件中提取统计数据,按instruction_type分类统计
"""
import os
import json
import argparse
from collections import defaultdict
from typing import Dict, List, Any


def calculate_statistics(eval_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    计算整体统计数据

    Args:
        eval_results: 评估结果列表

    Returns:
        统计数据字典
    """
    if not eval_results:
        return {
            'total_tasks': 0,
            'total_test_cases': 0,
            'passed_test_cases': 0,
            'soft_restriction_sum': 0.0,
            'hard_restriction_sum': 0,
        }

    total_tasks = len(eval_results)
    total_test_cases = sum(len(r['test_case_results']) for r in eval_results)
    passed_test_cases = sum(sum(r['test_case_results']) for r in eval_results)
    soft_restriction_sum = sum(r['soft_restriction'] for r in eval_results)
    hard_restriction_sum = sum(r['hard_restriction'] for r in eval_results)

    return {
        'total_tasks': total_tasks,
        'total_test_cases': total_test_cases,
        'passed_test_cases': passed_test_cases,
        'soft_restriction_sum': soft_restriction_sum,
        'hard_restriction_sum': hard_restriction_sum,
    }


def calculate_statistics_by_type(eval_results: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    按instruction_type计算统计数据

    Args:
        eval_results: 评估结果列表

    Returns:
        按类型分组的统计数据字典
    """
    # 按instruction_type分组
    results_by_type = defaultdict(list)
    for result in eval_results:
        instruction_type = result.get('instruction_type', 'Unknown')
        results_by_type[instruction_type].append(result)

    # 计算每个类型的统计数据
    stats_by_type = {}
    for instruction_type, results in results_by_type.items():
        stats_by_type[instruction_type] = calculate_statistics(results)

    return stats_by_type


def format_number(value: float) -> str:
    """格式化数值"""
    if isinstance(value, int):
        return str(value)
    return f"{value:.2f}"


def print_table(stats_overall: Dict[str, Any], stats_by_type: Dict[str, Dict[str, Any]], eval_results: List[Dict[str, Any]]):
    """
    打印统计表格

    Args:
        stats_overall: 整体统计数据
        stats_by_type: 按类型分组的统计数据
        eval_results: 评估结果列表
    """
    # 表格宽度
    col_widths = [30, 15, 15, 15, 18, 18]

    # 表头
    print("\n" + "=" * sum(col_widths))
    print("SpreadsheetBench 评估统计报告")
    print("=" * sum(col_widths))

    # 整体统计
    print("\n【整体统计】")
    print(f"  总任务数:          {stats_overall['total_tasks']}")
    print(f"  总测试用例数:      {stats_overall['total_test_cases']}")
    print(f"  通过测试用例数:    {stats_overall['passed_test_cases']}")
    print(f"  软限制总分:        {format_number(stats_overall['soft_restriction_sum'])}")
    print(f"  硬限制总分:        {stats_overall['hard_restriction_sum']}")

    # 按类型统计表格
    print("\n【按指令类型统计】")
    print("-" * sum(col_widths))

    # 表头
    headers = ["指令类型", "任务数", "测试用例数", "通过用例数", "软限制(总分)", "硬限制(总分)"]
    header_line = ""
    for i, header in enumerate(headers):
        header_line += header.ljust(col_widths[i], " ")
    print(header_line)
    print("-" * sum(col_widths))

    # 数据行
    for instruction_type, stats in sorted(stats_by_type.items()):
        row = [
            instruction_type,
            str(stats['total_tasks']),
            str(stats['total_test_cases']),
            str(stats['passed_test_cases']),
            format_number(stats['soft_restriction_sum']),
            str(stats['hard_restriction_sum']),
        ]
        row_line = ""
        for i, cell in enumerate(row):
            row_line += cell.ljust(col_widths[i], " ")
        print(row_line)

    print("-" * sum(col_widths))

    # 详细分析
    print("\n【详细分析】")
    for instruction_type, stats in sorted(stats_by_type.items()):
        print(f"\n  {instruction_type}:")
        print(f"    - 任务数: {stats['total_tasks']}")
        print(f"    - 测试用例通过: {stats['passed_test_cases']}/{stats['total_test_cases']}")
        print(f"    - 软限制总分: {format_number(stats['soft_restriction_sum'])}")
        print(f"    - 硬限制总分: {stats['hard_restriction_sum']}")

        # 计算分布
        results = [r for r in eval_results if r.get('instruction_type') == instruction_type]
        perfect_scores = sum(1 for r in results if r['hard_restriction'] == 1)
        partial_scores = sum(1 for r in results if 0 < r['soft_restriction'] < 1)
        zero_scores = sum(1 for r in results if r['soft_restriction'] == 0)

        print(f"    - 全部通过: {perfect_scores}")
        print(f"    - 部分通过: {partial_scores}")
        print(f"    - 全部失败: {zero_scores}")

    print("\n" + "=" * sum(col_widths))


def export_to_json(stats_overall: Dict[str, Any], stats_by_type: Dict[str, Dict[str, Any]], output_path: str):
    """
    导出统计结果到JSON文件

    Args:
        stats_overall: 整体统计数据
        stats_by_type: 按类型分组的统计数据
        output_path: 输出文件路径
    """
    output_data = {
        'overall': stats_overall,
        'by_instruction_type': stats_by_type
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n统计结果已导出到: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='从评估结果JSON文件中提取统计数据,按instruction_type分类统计',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本用法
  python statistics.py --input ../outputs/eval_single_model.json

  # 导出统计结果到JSON
  python statistics.py --input ../outputs/eval_single_model.json --export stats_output.json

  # 指定详细级别
  python statistics.py --input ../outputs/eval_single_model.json --verbose
        """
    )

    parser.add_argument(
        '--input', '-i',
        type=str,
        required=True,
        help='评估结果JSON文件路径'
    )

    parser.add_argument(
        '--export', '-e',
        type=str,
        default=None,
        help='导出统计结果到JSON文件(可选)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细信息'
    )

    args = parser.parse_args()

    # 检查输入文件是否存在
    if not os.path.exists(args.input):
        print(f"错误: 文件不存在: {args.input}")
        return

    # 读取评估结果
    if args.verbose:
        print(f"正在读取评估结果: {args.input}")

    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            eval_results = json.load(f)
    except json.JSONDecodeError as e:
        print(f"错误: JSON解析失败: {e}")
        return
    except Exception as e:
        print(f"错误: 读取文件失败: {e}")
        return

    if args.verbose:
        print(f"成功读取 {len(eval_results)} 条评估记录")

    # 计算统计数据
    stats_overall = calculate_statistics(eval_results)
    stats_by_type = calculate_statistics_by_type(eval_results)

    # 打印统计表格
    print_table(stats_overall, stats_by_type, eval_results)

    # 导出到JSON(如果指定)
    if args.export:
        export_to_json(stats_overall, stats_by_type, args.export)


if __name__ == '__main__':
    main()
