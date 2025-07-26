# 文件名: core/map_manager.py

import os
from collections import Counter
from core.db_manager import DBManager
from core.bml_parser import bml_to_xml_element

class MapManager:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MapManager, cls).__new__(cls)
            cls._instance.db = DBManager()
        return cls._instance

    def _aggregate_data(self, temp_path):
        """
        最终的数据聚合流程：
        1. 从 track@zz.bml 建立元数据基础 (难度、gameType as tag)。
        2. 从 trackLocale@*.bml 填充多语言译名。
        3. 从地图ID中解析根本类型。
        """
        master_map_data = {}
        
        # 1. 解析 track@zz.bml 获取元数据
        zz_bml_path = os.path.join(temp_path, "track_common.rho", "track@zz.bml")
        if os.path.exists(zz_bml_path):
            try:
                zz_root = bml_to_xml_element(zz_bml_path)
                elements_to_search = zz_root.findall(".//track") + zz_root.findall(".//track_crz") + zz_root.findall(".//track_rvs")
                for elem in elements_to_search:
                    track_id = elem.get('id') or elem.get('refId')
                    if not track_id: continue
                    track_id = track_id.strip()
                    
                    if track_id not in master_map_data:
                         master_map_data[track_id] = {'id': track_id, 'translations': {}, 'has_reverse_mode': False, 'tags': []}

                    # 将 gameType 作为一个标签(tag)存入
                    gt_from_zz = elem.get('gameType')
                    if gt_from_zz and gt_from_zz not in master_map_data[track_id]['tags']:
                        master_map_data[track_id]['tags'].append(gt_from_zz)
                    
                    if elem.tag == 'track':
                        master_map_data[track_id]['difficulty'] = elem.get('difficulty')

            except Exception as e:
                print(f"警告: 解析 track@zz.bml 失败: {e}")

        # 2. 解析 trackLocale@*.bml 填充译名
        bml_search_dir = os.path.join(temp_path, "track_common.rho")
        if os.path.exists(bml_search_dir):
            for f in os.listdir(bml_search_dir):
                if f.startswith('trackLocale@') and f.endswith('.bml'):
                    lang_code = f.split('@')[1].split('.')[0]
                    try:
                        root = bml_to_xml_element(os.path.join(bml_search_dir, f))
                        elements = root.findall(".//track") + root.findall(".//track_crz")
                        for elem in elements:
                            track_id = elem.get('id')
                            if not track_id: continue
                            track_id = track_id.strip()
                            if track_id in master_map_data:
                                name = elem.get('name')
                                if name and name.strip():
                                    master_map_data[track_id]['translations'][lang_code] = name.strip()
                        
                        for elem in root.findall('track_rvs'):
                            ref_id = elem.get('refId')
                            if ref_id and ref_id.strip() in master_map_data:
                                master_map_data[ref_id.strip()]['has_reverse_mode'] = True
                    except Exception as e:
                        print(f"警告: 处理 {f} 失败: {e}")
        
        # 3. 从ID中解析根本类型
        for track_id, data in master_map_data.items():
            parts = track_id.split('_')
            # 确保ID至少有两部分 (theme_type)
            if len(parts) > 1 and parts[1]:
                mode_char = parts[1][0]
                data['game_type'] = mode_char # 直接存入字母 R, I, S, D...
            else:
                data['game_type'] = 'O' # Fallback for unknown format
            
        return master_map_data

    def process_unpacked_data(self, temp_path, progress_callback=None):
        def report_progress(message, level='INFO'):
            if progress_callback: progress_callback(message, level)
            else: print(f"[{level}] {message}")
        
        master_data = self._aggregate_data(temp_path)
        report_progress(f"聚合完成，共找到 {len(master_data)} 条独特的地图ID。", "INFO")
        
        themes_with_names = {}
        if master_data:
            map_list = list(master_data.values())
            
            theme_name_candidates = {}
            for map_item in map_list:
                parts = map_item['id'].split('_')
                if parts:
                    theme_code = parts[0]
                    if theme_code not in theme_name_candidates:
                        theme_name_candidates[theme_code] = []
                    cn_name = map_item.get('translations', {}).get('cn')
                    if cn_name:
                        # 移除 "[奔跑车手]" 这样的前缀
                        clean_name = cn_name.split(']')[-1].strip()
                        theme_name_candidates[theme_code].append(clean_name.split(' ')[0])
            
            for theme_code, names in theme_name_candidates.items():
                if names:
                    most_common_name = Counter(names).most_common(1)[0][0]
                    if "模式" not in most_common_name and "竞技场" not in most_common_name:
                        themes_with_names[theme_code] = most_common_name
            
            self.db.save_maps_batch(map_list)
            report_progress("地图数据已存入数据库。", "INFO")
        else:
            report_progress("没有聚合到任何地图数据，数据库未更新。", "WARNING")
            
        return {'count': len(master_data), 'themes_data': themes_with_names}