# 文件名: core/language_service_placeholder.py (V5 - 增加地图类型翻译)

class LanguageServicePlaceholder:
    def __init__(self):
        # ... (主题和UI字符串数据不变) ...
        self.themes = {"forest": "森林", "ice": "冰河", "desert": "沙漠", "village": "城镇", "tomb": "墓地",
                       "mine": "矿山", "northeu": "太空", "factory": "工厂", "pirate": "海盗", "fairy": "童话世界",
                       "moonhill": "月光之城", "gold": "黄金文明", "china": "龙行华夏", "castle": "大城堡",
                       "nymph": "精灵", "mechanic": "机械", "wkc": "WKC", "brodi": "未来工厂", "park": "跑跑游乐场",
                       "beach": "滨海大道", "steam": "1920", "jurassic": "侏罗纪", "world": "环游世界",
                       "nemo": "像素世界", "sword": "刀剑", "god": "神之国度", "abyss": "深渊之都",
                       "camelot": "亚瑟传说", "olympos": "奥林匹斯", "xyy": "喜羊羊"}
        self.ui_strings = {"map_prefixes.reverse_cn": "[反]", "map_prefixes.reverse_tw": "[反方向]",
                           "map_prefixes.reverse_kr": "[R]", "map_prefixes.reverse_en": "[R]"}

        # --- 核心修改: 新增地图类型翻译字典 ---
        self.map_types = {
            'R': '竞速', 'I': '道具', 'S': '故事', 'D': '死斗',
            'C': '道具(C)', 'K': 'BOSS战', 'F': '夺旗'
        }

        self.current_lang = 'cn'
        self.fallback_order = ['cn', 'tw', 'kr', 'en']

    # --- 核心修改: 补上缺失的方法 ---
    def get_map_type_name(self, type_code, fallback="其他"):
        """根据单字母类型码获取本地化名称"""
        # TODO: 真实的实现会根据self.current_lang返回不同语言的翻译
        return self.map_types.get(type_code, fallback)

    def find_untranslated_themes(self, discovered_themes):
        return [theme for theme in discovered_themes if theme not in self.themes]

    def update_theme_translations(self, new_themes_data: dict):
        print("信息: 正在模拟更新主题翻译...")
        if not new_themes_data:
            print("警告: 未能为新主题找到合适的默认中文名。")
            return
        self.themes.update(new_themes_data)
        print(f"成功添加了以下新主题翻译: {new_themes_data}")

    def tr(self, key):
        lang_key = f"{key}_{self.current_lang}"
        return self.ui_strings.get(lang_key, self.ui_strings.get(f"{key}_cn", f"[{key}]"))

    def get_theme_name(self, theme_code, fallback=""):
        return self.themes.get(theme_code, fallback)

    def get_map_name_with_fallback(self, map_item):
        for lang_code in self.fallback_order:
            lang_key = f"name_{lang_code}"
            if map_item.get(lang_key):
                return map_item[lang_key]
        return map_item.get('id', '[未知地图]')


i18n = LanguageServicePlaceholder()