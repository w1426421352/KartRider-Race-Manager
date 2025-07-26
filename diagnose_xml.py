import sys
import os
import traceback
from bs4 import BeautifulSoup
from lxml import etree
import chardet


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_direct_read(filepath, encoding):
    """测试直接用指定的文本编码读取文件"""
    print_header(f"测试 1: 直接以 '{encoding}' 文本编码读取")
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            content = f.read(256)  # 只读取前256个字符作为样本
            print(f"✅ 成功: 文件可以用 '{encoding}' 编码读取。")
            print(f"文件内容开头: \n---\n{content}\n---")
            return True
    except Exception as e:
        print(f"❌ 失败: 尝试用 '{encoding}' 编码读取时发生错误。")
        print("\n--- 完整错误报告 ---")
        traceback.print_exc()
        print("--- 错误报告结束 ---\n")
        return False


def test_binary_analysis(filepath):
    """分析文件的二进制头部，并用chardet检测"""
    print_header("测试 2: 二进制分析")
    try:
        with open(filepath, 'rb') as f:
            raw_bytes = f.read()

            # 打印文件前64个字节的十六进制表示
            hex_dump = ' '.join(f'{b:02x}' for b in raw_bytes[:64])
            print(f"文件二进制头部 (前64字节): \n{hex_dump}")

            if raw_bytes.startswith(b'\xff\xfe'):
                print("发现BOM: FF FE -> UTF-16 Little Endian")
            elif raw_bytes.startswith(b'\xfe\xff'):
                print("发现BOM: FE FF -> UTF-16 Big Endian")
            elif raw_bytes.startswith(b'\xef\xbb\xbf'):
                print("发现BOM: EF BB BF -> UTF-8")
            else:
                print("未发现标准BOM。")

            # Chardet检测
            detection = chardet.detect(raw_bytes)
            print(f"Chardet检测结果: {detection}")
            return True

    except Exception as e:
        print("❌ 失败: 读取二进制内容时发生错误。")
        print("\n--- 完整错误报告 ---")
        traceback.print_exc()
        print("--- 错误报告结束 ---\n")
        return False


def test_parsing(filepath, encoding, parser_lib):
    """测试用指定的库和编码解析文件"""
    print_header(f"测试 3: 使用 '{parser_lib}' 库以 '{encoding}' 编码解析")
    content = None
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            content = f.read()
    except Exception as e:
        print(f"❌ 失败: 在解析前，用 '{encoding}' 编码读取文件时已发生错误。")
        print("\n--- 完整错误报告 ---")
        traceback.print_exc()
        print("--- 错误报告结束 ---\n")
        return False

    if content:
        try:
            if parser_lib == 'BeautifulSoup-xml':
                soup = BeautifulSoup(content, 'xml')
                tags_found = len(soup.find_all(['track', 'track_rvs', 'track_crz']))
                print(f"✅ 成功: 使用 BeautifulSoup (xml解析器) 解析成功。")
                print(f"找到了 {tags_found} 个地图相关标签。")

            elif parser_lib == 'lxml-recover':
                parser = etree.XMLParser(recover=True, encoding=encoding)
                # lxml需要二进制流
                tree = etree.fromstring(content.encode(encoding), parser=parser)
                tags_found = len(tree.xpath('//*[self::track or self::track_rvs or self::track_crz]'))
                print(f"✅ 成功: 使用 lxml (recover模式) 解析成功。")
                print(f"找到了 {tags_found} 个地图相关标签。")

            return True

        except Exception as e:
            print(f"❌ 失败: 使用 '{parser_lib}' 解析时发生错误。")
            print("\n--- 完整错误报告 ---")
            traceback.print_exc()
            print("--- 错误报告结束 ---\n")
            return False


def main():
    if len(sys.argv) < 2:
        print("错误: 请提供一个文件名作为参数。")
        print("用法: python diagnose_xml.py trackLocale@cn.xml")
        sys.exit(1)

    filepath = sys.argv[1]

    if not os.path.exists(filepath):
        print(f"错误: 文件 '{filepath}' 不存在。")
        sys.exit(1)

    print(f"开始对文件 '{filepath}' 进行诊断...")

    # --- 执行一系列诊断测试 ---

    # 1. 二进制分析先行，获取文件底层信息
    test_binary_analysis(filepath)

    # 2. 尝试我们之前假设的所有编码
    test_direct_read(filepath, 'utf-16')
    test_direct_read(filepath, 'utf-8-sig')

    if 'cn.xml' in filepath:
        test_direct_read(filepath, 'gbk')
    elif 'tw.xml' in filepath:
        test_direct_read(filepath, 'big5')
    elif 'kr.xml' in filepath:
        test_direct_read(filepath, 'euc-kr')

    # 3. 尝试用最有可能的编码和强大的解析器进行解析
    # 基于之前的分析，utf-16是最可能的正确编码
    test_parsing(filepath, 'utf-16', 'BeautifulSoup-xml')
    test_parsing(filepath, 'utf-16', 'lxml-recover')

    print("\n" + "*" * 70)
    print("诊断完成。请将以上所有输出信息完整地复制并发送给我。")
    print("*" * 70)


if __name__ == '__main__':
    main()