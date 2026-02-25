"""
股票名称映射模块
"""
import json
import os
import logging

logger = logging.getLogger(__name__)

# 加载股票名称映射
STOCK_NAMES = {}
try:
    json_path = os.path.join(os.path.dirname(__file__), "..", "stock_names.json")
    with open(json_path, "r", encoding="utf-8") as f:
        STOCK_NAMES = json.load(f)
    logger.info(f"✅ 加载了 {len(STOCK_NAMES)} 个股票名称")
except Exception as e:
    logger.warning(f"⚠️ 无法加载股票名称文件: {e}")


def get_stock_name(code: str) -> str:
    """
    获取股票中文名称
    
    Args:
        code: 股票代码，可以是 "600519" 或 "600519.SS"
    
    Returns:
        str: 股票中文名称，如果找不到则返回代码本身
    """
    # 移除后缀
    clean_code = code.replace(".SS", "").replace(".SZ", "")
    return STOCK_NAMES.get(clean_code, clean_code)
