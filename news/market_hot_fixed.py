"""
news/market_hot.py
行情数据模块 - 修复版，添加股票名称映射
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

try:
    import yfinance as yf
    YF_OK = True
except ImportError:
    YF_OK = False
    logger.error("yfinance 未安装！")


@dataclass
class IndexSnapshot:
    name: str
    price: float
    change_pct: float
    prev_close: float = 0.0


@dataclass
class SectorInfo:
    name: str
    change_pct: float
    etf_code: str = ""
    hot_reason: str = ""


@dataclass
class StockHotInfo:
    code: str
    name: str
    price: float
    change_pct: float
    volume_ratio: float = 1.0


# 股票代码到名称的映射
STOCK_NAME_MAP = {
    "600519": "贵州茅台", "000858": "五粮液", "300750": "宁德时代",
    "601318": "中国平安", "600036": "招商银行", "000001": "平安银行",
    "600276": "恒瑞医药", "000333": "美的集团", "002594": "比亚迪",
    "688981": "中芯国际", "002475": "立讯精密", "601012": "隆基绿能",
    "600900": "长江电力", "688111": "金山办公", "601888": "中国中免",
    "300015": "爱尔眼科", "603288": "海天味业", "002460": "赣锋锂业",
    "000651": "格力电器", "601166": "兴业银行", "300760": "迈瑞医疗",
    "600031": "三一重工", "002714": "牧原股份", "600309": "万华化学",
    "002049": "紫光股份", "600887": "伊利股份", "002858": "路畅科技",
    "300144": "宋城演艺", "601939": "建设银行", "000002": "万科A",
}

INDEX_MAP = {
    "上证指数": "000001.SS", "深证成指": "399001.SZ", "创业板指": "399006.SZ",
    "沪深300": "000300.SS", "科创50": "000688.SS", "恒生指数": "^HSI",
    "道琼斯": "^DJI", "纳斯达克": "^IXIC", "标普500": "^GSPC",
}

SECTOR_ETF_MAP = {
    "新能源": "159806.SZ", "半导体": "512480.SS", "人工智能": "159819.SZ",
    "医药生物": "512010.SS", "消费电子": "159995.SZ", "军工": "512660.SS",
    "银行": "512800.SS", "食品饮料": "159869.SZ", "有色金属": "512400.SS",
    "光伏": "515790.SS", "储能": "562790.SZ", "创新药": "159992.SZ",
}


def fetch_market_overview() -> Dict[str, IndexSnapshot]:
    """拉取全球主要指数快照"""
    result: Dict[str, IndexSnapshot] = {}
    tickers = list(INDEX_MAP.values())
    
    logger.info(f"拉取 {len(tickers)} 个指数行情...")
    try:
        tickers_obj = yf.Tickers(" ".join(tickers))
        for name, code in INDEX_MAP.items():
            try:
                t = tickers_obj.tickers[code]
                fi = t.fast_info
                price = round(fi.last_price or 0, 2)
                prev = round(fi.previous_close or price, 2)
                chg = round((price - prev) / prev * 100, 2) if prev else 0.0
                result[name] = IndexSnapshot(
                    name=name, price=price, change_pct=chg, prev_close=prev
                )
            except Exception as e:
                logger.debug(f"指数 {name}({code}) 获取失败: {e}")
    except Exception as e:
        logger.error(f"指数批量获取失败: {e}")
    
    logger.info(f"指数获取完成: {len(result)}/{len(INDEX_MAP)}")
    return result


def fetch_hot_sectors(top_n: int = 6) -> List[SectorInfo]:
    """用行业 ETF 涨跌幅代理热门板块"""
    sectors: List[SectorInfo] = []
    logger.info(f"拉取行业 ETF 涨跌幅（{len(SECTOR_ETF_MAP)} 个）...")
    
    for sector_name, etf_code in SECTOR_ETF_MAP.items():
        try:
            t = yf.Ticker(etf_code)
            fi = t.fast_info
            price = fi.last_price or 0
            prev = fi.previous_close or price
            chg = round((price - prev) / prev * 100, 2) if prev else 0.0
            sectors.append(SectorInfo(
                name=sector_name,
                change_pct=chg,
                etf_code=etf_code,
                hot_reason="行业ETF代理",
            ))
        except Exception as e:
            logger.debug(f"ETF {etf_code} 失败: {e}")
    
    sectors.sort(key=lambda x: x.change_pct, reverse=True)
    top = sectors[:top_n]
    logger.info(f"热门板块: {[f'{s.name}({s.change_pct:+.2f}%)' for s in top]}")
    return top


def fetch_hot_stocks(stock_pool: List[str], top_n: int = 8) -> List[StockHotInfo]:
    """从监控池中筛选今日涨幅最高的股票"""
    def to_yf(code: str) -> str:
        if "." in code:
            return code
        return f"{code}.SS" if code.startswith("6") or code.startswith("9") else f"{code}.SZ"
    
    def get_stock_name(code: str) -> str:
        """获取股票名称"""
        clean_code = code.split(".")[0]
        return STOCK_NAME_MAP.get(clean_code, clean_code)
    
    yf_codes = [to_yf(c) for c in stock_pool[:80]]
    hot: List[StockHotInfo] = []
    
    logger.info(f"拉取股票池行情（{len(yf_codes)} 支）...")
    try:
        raw = yf.download(
            yf_codes, period="2d", interval="1d",
            auto_adjust=True, progress=False, threads=True,
        )
        close_df = raw["Close"] if "Close" in raw else None
        if close_df is None:
            raise ValueError("无法获取收盘价数据")
        
        for yf_code, cn_code in zip(yf_codes, stock_pool[:80]):
            try:
                series = close_df[yf_code].dropna()
                if len(series) < 2:
                    continue
                prev_close = float(series.iloc[-2])
                today_close = float(series.iloc[-1])
                if prev_close == 0:
                    continue
                chg = round((today_close - prev_close) / prev_close * 100, 2)
                
                clean_code = cn_code.split(".")[0]
                name = get_stock_name(clean_code)
                
                hot.append(StockHotInfo(
                    code=clean_code,
                    name=name,
                    price=round(today_close, 2),
                    change_pct=chg,
                    volume_ratio=1.0,
                ))
            except Exception:
                continue
    
    except Exception as e:
        logger.warning(f"股票批量获取失败: {e}")
    
    hot.sort(key=lambda x: x.change_pct, reverse=True)
    result = [s for s in hot if 2 <= s.change_pct <= 19.9][:top_n]
    logger.info(f"热门股票 Top-{len(result)}: {[f'{s.name}({s.change_pct:+.2f}%)' for s in result]}")
    return result


def fetch_north_fund_flow() -> Dict[str, Any]:
    """获取北向资金流向数据（模拟）"""
    logger.warning("北向资金数据暂不可用,返回模拟数据")
    return {
        "today_net": 0.0,
        "week_net": 0.0,
        "month_net": 0.0,
    }
