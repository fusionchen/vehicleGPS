# -*- coding: utf-8 -*-
"""
用于确定脚本文件所在文件目录
确定数据文件所在目录
"""
__author__ = "张巍汉"

import os
import platform

system_type = platform.system()

# 获取项目根目录
PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
# 保持数据文件的文件夹路径
file_path = os.path.split(os.path.split(PROJECT_ROOT)[0])[0]
# 文件路径
if system_type == 'Windows':
    data_file_path = os.path.join(file_path, "Data\\sichuan-xcar-2016080810.csv")
if system_type == 'Linux':
    data_file_path = os.path.join(file_path, "Data/sichuan-xcar-2016080810.csv")