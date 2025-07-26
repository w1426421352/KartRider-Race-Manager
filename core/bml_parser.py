# 文件名: core/bml_parser.py

import struct
import os
from xml.etree.ElementTree import Element, SubElement


def _read_int32(file):
    """从文件中读取一个32位小端整数"""
    return struct.unpack('<i', file.read(4))[0]


def _read_bml_string(file):
    """读取BML格式的字符串（长度前缀 + UTF-16LE）"""
    char_count = _read_int32(file)
    if char_count <= 0:
        return ""
    byte_count = char_count * 2
    return file.read(byte_count).decode('utf-16-le')


def _parse_bml_node(file):
    """
    递归地解析一个BML节点及其所有子节点。
    返回一个 xml.etree.ElementTree.Element 对象。
    """
    element_name = _read_bml_string(file)
    if not element_name:
        return None

    node = Element(element_name)

    # 在 BML 格式中，节点名后紧跟一个文本字段，通常为空
    node.text = _read_bml_string(file)

    # 读取属性
    attr_count = _read_int32(file)
    for _ in range(attr_count):
        attr_name = _read_bml_string(file)
        attr_value = _read_bml_string(file)
        node.set(attr_name, attr_value)

    # 递归读取子节点
    child_count = _read_int32(file)
    for _ in range(child_count):
        child_node = _parse_bml_node(file)
        if child_node is not None:
            node.append(child_node)

    return node


def bml_to_xml_element(bml_path: str) -> Element:
    """
    将指定的 .bml 文件完整地转换为一个 ElementTree 对象。
    这是对外暴露的主接口。
    """
    print(f"信息: 正在用Python解析BML文件: {os.path.basename(bml_path)}")
    try:
        with open(bml_path, 'rb') as f:
            root_node = _parse_bml_node(f)
            if root_node is None:
                raise ValueError("无法解析BML文件，可能文件为空或格式不正确。")
            return root_node
    except FileNotFoundError:
        raise
    except Exception as e:
        print(f"错误: BML文件 '{bml_path}' 解析失败: {e}")
        raise