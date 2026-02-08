#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动生成所有主板股票的中文名称
对于没有真实名称的股票，使用"上交所/深交所+代码"格式
"""

import json
import os

# 从stock_names.py导入已知的股票名称
try:
    from stock_names import STOCK_NAMES
    print(f"已加载 {len(STOCK_NAMES)} 只已知股票名称")
except:
    STOCK_NAMES = {}
    print("未找到stock_names.py，将生成全新映射")

# 生成所有可能的主板股票代码
all_stocks = {}

# 上海主板：600000-603999
for prefix in ['600', '601', '603']:
    for i in range(1000):
        code = f"{prefix}{i:03d}"
        if code in STOCK_NAMES:
            all_stocks[code] = STOCK_NAMES[code]
        else:
            all_stocks[code] = f"上交所{code}"

# 深圳主板：000000-002999
for prefix in ['000', '001', '002']:
    for i in range(1000):
        code = f"{prefix}{i:03d}"
        if code in STOCK_NAMES:
            all_stocks[code] = STOCK_NAMES[code]
        else:
            all_stocks[code] = f"深交所{code}"

# 保存为JSON
output_file = 'stock_list.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(all_stocks, f, ensure_ascii=False, indent=2)

print(f"\n✅ 已生成 {len(all_stocks)} 只股票的映射")
print(f"📁 保存到: {output_file}")
print(f"\n其中:")
print(f"  - 真实名称: {len(STOCK_NAMES)} 只")
print(f"  - 生成名称: {len(all_stocks) - len(STOCK_NAMES)} 只")
print(f"\n前10只股票示例:")
for i, (code, name) in enumerate(list(all_stocks.items())[:10]):
    print(f"  {code}: {name}")
