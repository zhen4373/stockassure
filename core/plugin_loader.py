import json
import os
from pathlib import Path
from core.config import settings

# 這是全域的記憶體快取字典
# 結構：
# {
#     "network_cable_template": {
#         "schema": {...},
#         "plugin_name": "NetworkPlugin",
#         "plugin_version": "1.0",
#         "plugin_path": "/path/to/plugins/NetworkPlugin"
#     }
# }
GLOBAL_TEMPLATES = {}

def load_plugins():
    global GLOBAL_TEMPLATES
    GLOBAL_TEMPLATES.clear()  # 每次載入前先清空，確保乾淨
    
    plugins_dir = settings.PLUGINS_DIR
    if not plugins_dir.exists():
        print(f"⚠️ 外掛目錄 {plugins_dir} 不存在，跳過載入。")
        return

    print("🔌 StockAssure 外掛引擎開始掃描...")
    
    # 遍歷 plugins/ 底下的所有第一層子目錄
    for entry in os.scandir(plugins_dir):
        if entry.is_dir():
            plugin_path = Path(entry.path)
            info_file = plugin_path / "plugin_config.json"
            
            # 檢查是否有身份證
            if not info_file.exists():
                continue
                
            try:
                with open(info_file, "r", encoding="utf-8") as f:
                    plugin_info = json.load(f)
                    plugin_name = plugin_info.get('name', plugin_path.name)
                    plugin_version = plugin_info.get('version', '1.0')
                
                # 檢查外掛是否被啟用 (enabled)
                if not plugin_info.get("enabled", False):
                    print(f"🚫 外掛 [{plugin_name}] 已被禁用，跳過。")
                    continue
                
                print(f"📦 發現已啟用外掛: {plugin_name} (v{plugin_version})")
                
                # 掃描該外掛底下的 templates/ 資料夾
                templates_dir = plugin_path / "templates"
                if templates_dir.exists() and templates_dir.is_dir():
                    for t_entry in os.scandir(templates_dir): # loop all template under 'template'
                        if t_entry.is_file() and t_entry.name.endswith(".json"):
                            template_path = Path(t_entry.path)
                            template_key = template_path.stem  # 拿檔名當作 Key (例如: network_cable_template)
                            
                            with open(template_path, "r", encoding="utf-8") as tf:
                                template_schema = json.load(tf)
                            
                            # 主動式模板名稱衝突檢測 (Collision Detection)
                            if template_key in GLOBAL_TEMPLATES:
                                conflict_target = GLOBAL_TEMPLATES[template_key]
                                print(f"⚠️ [衝突警告] 發現同名模板衝突！")
                                print(f"   🔥 模板 [{template_key}] 已先被外掛 [{conflict_target['plugin_name']}] (v{conflict_target['plugin_version']}) 載入。")
                                print(f"   🔥 來自外掛 [{plugin_name}] (v{plugin_version}) 的同名模板將會覆蓋它！請檢查外掛結構。")
                            
                            GLOBAL_TEMPLATES[template_key] = {
                                "schema": template_schema,
                                "plugin_name": plugin_name,
                                "plugin_version": plugin_version,
                                "plugin_path": str(plugin_path)
                            }
                            print(f"    └─ 🔌 已成功載入模板: [{template_key}]")
                            
            except Exception as e:
                print(f"❌ 載入外掛 {plugin_path.name} 失敗: {e}")

    print(f"\n🎉 外掛載入完畢！目前共啟用 {len(GLOBAL_TEMPLATES)} 個物資強校驗模板。")
    template_list()
    
def template_list():
    count = 0
    # 🌟 讀取完整的結構包，印出更具可讀性、包含版本號的外掛歸屬清單
    for template_name, template_data in GLOBAL_TEMPLATES.items():
        count += 1
        plugin = template_data.get("plugin_name", "Unknown Plugin")
        version = template_data.get("plugin_version", "1.0")
        print(f"    └─ {count}: {template_name} from [{plugin}] (v{version})")
