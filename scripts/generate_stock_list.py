#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成完整的A股主板股票列表
由于无法在GitHub Actions中使用AKShare，这个脚本需要在本地运行
"""

try:
    import akshare as ak
    import json

    print("正在获取全部A股列表...")

    # 获取全部 A 股
    df_all = ak.stock_info_a_code_name()
    print(f"获取到 {len(df_all)} 只股票")

    # 筛选主板股票
    mask_main = (
        df_all["code"].str.startswith(("600", "601", "603")) |  # 上交所主板
        df_all["code"].str.startswith(("000", "001", "002"))    # 深交所主板
    )
    df_main = df_all[mask_main].copy()
    print(f"筛选出 {len(df_main)} 只主板股票")

    # 生成字典
    stock_dict = dict(zip(df_main["code"], df_main["name"]))

    # 保存为JSON
    with open("stock_list.json", "w", encoding="utf-8") as f:
        json.dump(stock_dict, f, ensure_ascii=False, indent=2)

    print(f"✅ 已生成 stock_list.json，包含 {len(stock_dict)} 只股票")
    print("\n前10只股票示例：")
    for i, (code, name) in enumerate(list(stock_dict.items())[:10]):
        print(f"  {code}: {name}")

except ImportError:
    print("❌ 错误：未安装 akshare")
    print("请运行：pip install akshare")
except Exception as e:
    print(f"❌ 错误：{e}")
