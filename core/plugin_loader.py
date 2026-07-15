import json
import os
from pathlib import Path
from core.config import settings

# 這是全域的記憶體快取字典
# 結構：{"network_cable_template": { ...Schema 內容... }, "usb_cable_template": { ... }}
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
                    str(plugin_name) = plugin_info.get('name')
                
                # 檢查外掛是否被啟用 (enabled)
                if not plugin_info.get("enabled", False):
                    print(f"🚫 外掛 [plugin_mame] 已被禁用，跳過。")
                    continue
                
                print(f"📦 發現已啟用外掛: {plugin_name} (v{plugin_info.get('version')})")
                
                # 掃描該外掛底下的 templates/ 資料夾
                templates_dir = plugin_path / "templates"
                if templates_dir.exists() and templates_dir.is_dir():
                    for t_entry in os.scandir(templates_dir): #loop all template under 'template'
                        if t_entry.is_file() and t_entry.name.endswith(".json"):
                            template_path = Path(t_entry.path)
                            template_key = template_path.stem  # 拿檔名當作 Key (例如: network_cable_template)
                            
                            with open(template_path, "r", encoding="utf-8") as tf:
                                template_schema = json.load(tf)
                            
                            # 塞進全域記憶體
                            GLOBAL_TEMPLATES[template_key] = template_schema
                            print(f"   └─ 🔌 已成功載入模板: [{template_key}]")
                            
            except Exception as e:
                print(f"❌ 載入外掛 {plugin_path.name} 失敗: {e}")

    print(f"🎉 外掛載入完畢！目前共啟用 {len(GLOBAL_TEMPLATES)} 個物資強校驗模板。")
    template_list()
    
def template_list():
   count = 0
   for template_name in GLOBAL_TEMPLATES.keys():
        count += 1
        print(f"   └─ {count}:{template_name} from {}")
