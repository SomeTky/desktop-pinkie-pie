#!/usr/bin/env python3
"""
简单的图片缩放脚本
将输入图片（正方形 PNG）缩放到 150x150 像素并保存。
"""

import sys
from PIL import Image

def resize_image(input_path, output_path=None):
    """
    将 input_path 图片缩放到 150x150 像素，保存为 output_path。
    若未提供 output_path，则自动在原文件名后添加 "_150x150"。
    """
    try:
        # 打开图片
        with Image.open(input_path) as img:
            # 转换为 RGB（避免 PNG 透明通道问题，也可保留 RGBA）
            # 若需要保留透明，可注释下一行，但这里为了通用，保留原模式
            original_mode = img.mode
            # 缩放至 150x150（使用高质量重采样滤镜 LANCZOS）
            resized = img.resize((150, 150), Image.Resampling.LANCZOS)
            
            # 自动生成输出文件名
            if output_path is None:
                if input_path.lower().endswith('.png'):
                    output_path = input_path[:-4] + '_150x150.png'
                else:
                    output_path = input_path + '_150x150.png'
            
            # 保存，保持 PNG 格式
            resized.save(output_path, format='PNG')
            print(f"成功！原图已缩放至 150x150 并保存为：{output_path}")
    except FileNotFoundError:
        print(f"错误：找不到文件 '{input_path}'")
    except Exception as e:
        print(f"处理图片时出错：{e}")

if __name__ == "__main__":
    # 解析命令行参数
    if len(sys.argv) < 2:
        print("用法：python resize_image.py <输入图片路径> [输出图片路径]")
        print("示例：python resize_image.py input.png output.png")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    resize_image(input_file, output_file)