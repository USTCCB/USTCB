# 如何生成完整的股票名称列表

## 方法1：使用AKShare（推荐）

在本地运行以下命令生成完整的股票列表：

```bash
cd scripts
python generate_stock_list.py
```

这将生成 `stock_list.json` 文件，包含所有主板股票的中文名称。

## 方法2：手动运行代码

```python
import akshare as ak
import json

# 获取全部A股
df_all = ak.stock_info_a_code_name()

# 筛选主板股票
mask_main = (
    df_all["code"].str.startswith(("600", "601", "603")) |  # 上交所主板
    df_all["code"].str.startswith(("000", "001", "002"))    # 深交所主板
)
df_main = df_all[mask_main].copy()

# 生成字典并保存
stock_dict = dict(zip(df_main["code"], df_main["name"]))

with open("stock_list.json", "w", encoding="utf-8") as f:
    json.dump(stock_dict, f, ensure_ascii=False, indent=2)

print(f"已生成 {len(stock_dict)} 只股票的映射")
```

## 使用说明

1. 在本地运行上述代码生成 `stock_list.json`
2. 将生成的文件放到 `scripts/` 目录
3. 提交到GitHub
4. 系统会自动加载这个文件

## 当前状态

- ✅ 内置300+只常见股票映射
- ⚠️ 如果没有 `stock_list.json`，其他股票显示为"沪市/深市+代码"
- 📝 生成完整列表后，所有股票都将显示真实中文名称
