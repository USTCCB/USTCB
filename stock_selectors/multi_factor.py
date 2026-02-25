"""
selectors/multi_factor.py  — GitHub Actions 兼容版
"""
import logging, time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np

logger = logging.getLogger(__name__)

try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False
    logger.warning("yfinance 未安装，将使用演示数据")


# 使用外部股票名称文件
from stock_selectors.stock_names import get_stock_name as _get_stock_name

STOCK_NAME_MAP_OLD = {
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


def get_stock_name(code: str) -> str:
    return _get_stock_name(code)

def get_stock_name_old(code: str) -> str:
    clean_code = code.replace(".SS", "").replace(".SZ", "")
    return STOCK_NAME_MAP.get(clean_code, clean_code)


@dataclass
class StockScore:
    code: str
    name: str
    price: float
    change_pct: float
    total_score: float
    factor_scores: Dict[str, float] = field(default_factory=dict)
    buy_reason: str = ""
    risk_tip: str = ""
    pe: float = 0.0
    volume_ratio: float = 0.0


CANDIDATE_STOCKS = [
    ("600519.SS","贵州茅台","白酒"), ("300750.SZ","宁德时代","新能源"),
    ("601318.SS","中国平安","金融"), ("000858.SZ","五粮液","白酒"),
    ("600036.SS","招商银行","银行"), ("002594.SZ","比亚迪","汽车"),
    ("601012.SS","隆基绿能","光伏"), ("000333.SZ","美的集团","家电"),
    ("002415.SZ","海康威视","安防"), ("600900.SS","长江电力","电力"),
    ("688111.SS","金山办公","软件"), ("000001.SZ","平安银行","银行"),
    ("601888.SS","中国中免","免税"), ("300015.SZ","爱尔眼科","医疗"),
    ("603288.SS","海天味业","食品"), ("002460.SZ","赣锋锂业","锂电"),
    ("000651.SZ","格力电器","家电"), ("601166.SS","兴业银行","银行"),
    ("600276.SS","恒瑞医药","医药"), ("300760.SZ","迈瑞医疗","医疗"),
    ("600031.SS","三一重工","工程"),("688981.SS","中芯国际","半导体"),
    ("002714.SZ","牧原股份","农业"), ("600309.SS","万华化学","化工"),
    ("002049.SZ","紫光股份","信创"), ("600887.SS","伊利股份","食品"),
    ("002858.SZ","路畅科技","汽车电子"),("300144.SZ","宋城演艺","文旅"),
    ("601939.SS","建设银行","银行"), ("000002.SZ","万科A","地产"),
]


def _ema(data, n):
    k, r = 2/(n+1), [data[0]]
    for v in data[1:]: r.append(v*k + r[-1]*(1-k))
    return r

def _macd(close, fast=12, slow=26, sig=9):
    dif = [f-s for f,s in zip(_ema(close,fast), _ema(close,slow))]
    dea = _ema(dif, sig)
    return dif, dea

def _rsi(close, p=14):
    g=[max(close[i]-close[i-1],0) for i in range(1,len(close))]
    l=[max(close[i-1]-close[i],0) for i in range(1,len(close))]
    if len(g)<p: return 50.0
    ag,al = sum(g[-p:])/p, sum(l[-p:])/p
    return 100 if al==0 else 100-100/(1+ag/al)

def _boll_pos(close, p=20):
    if len(close)<p: return 0.5
    r=close[-p:]; mid=sum(r)/p; std=(sum((x-mid)**2 for x in r)/p)**.5
    return (close[-1]-(mid-2*std))/((4*std)+1e-9)


def _score_one(close,high,low,volume,pe,weights):
    if len(close)<30: return None
    s={}
    s["momentum_5d"]  = float(np.clip((( close[-1]-close[-6])/close[-6]+0.08)/0.16,0,1))
    s["momentum_20d"] = float(np.clip(((close[-1]-close[-21])/close[-21]+0.12)/0.24,0,1))
    avg_v = sum(volume[-21:-1])/20 if len(volume)>=21 else sum(volume)/len(volume)
    vr = volume[-1]/(avg_v+1)
    s["volume_ratio"] = float(np.clip((vr-0.5)/3.5,0,1))
    dif,dea = _macd(close)
    cross = dif[-2]<dea[-2] and dif[-1]>dea[-1]
    s["macd_signal"] = 1.0 if cross else (0.5 if dif[-1]>dea[-1] else 0.0)
    rsi=_rsi(close)
    s["rsi_score"] = 1.0 if 40<=rsi<=65 else (0.6 if 30<=rsi<=75 else (0.3 if rsi<30 else 0.1))
    if len(close)>=9:
        ln,hn=min(low[-9:]),max(high[-9:])
        rsv=(close[-1]-ln)/(hn-ln+1e-9)*100
        K=rsv*(2/3)+50*(1/3); D=K*(2/3)+50*(1/3)
        s["kdj_signal"] = 1.0 if K>D and K<80 else 0.3
    else: s["kdj_signal"]=0.5
    s["boll_position"] = float(np.clip(_boll_pos(close),0,1))
    rv5=volume[-1]/(sum(volume[-6:-1])/5+1) if len(volume)>=6 else 1
    s["turnover_rate"] = float(np.clip((rv5-0.8)/2.0,0,1))
    if   0<pe<=20:  s["pe_score"]=1.0
    elif 20<pe<=40: s["pe_score"]=0.7
    elif 40<pe<=70: s["pe_score"]=0.4
    elif pe>70:     s["pe_score"]=0.1
    else:           s["pe_score"]=0.5
    s["north_flow"]=0.5
    return s


def _total(fs,weights):
    t=w=0.0
    for k,wt in weights.items(): t+=fs.get(k,0.5)*wt; w+=wt
    return round(t/w if w else 0,4)

def _reason(s):
    t=[]
    if s.get("macd_signal",0)>=0.8: t.append("MACD金叉")
    if s.get("kdj_signal",0)>=0.8:  t.append("KDJ多头")
    if s.get("volume_ratio",0)>=0.65:t.append("放量上涨")
    if s.get("momentum_5d",0)>=0.7: t.append("短线强势")
    if s.get("momentum_20d",0)>=0.7:t.append("中期趋势向上")
    if s.get("pe_score",0)>=0.8:    t.append("低估值")
    return "、".join(t) or "多因子综合评分较高"

def _risk(s):
    t=[]
    if s.get("rsi_score",0)<=0.15:  t.append("RSI超买注意回调")
    if s.get("momentum_5d",0)>=0.88:t.append("短线涨幅较大")
    if s.get("volume_ratio",0)>=0.92:t.append("量能极度放大需警惕")
    return "；".join(t) or "风险适中"


def run_selector(weights, top_n=10, stock_pool=None):
    if not YF_AVAILABLE:
        return _demo(top_n)

    pool = CANDIDATE_STOCKS
    if stock_pool:
        pool = []
        for c in stock_pool:
            if "." in c:
                yf_code = c
                clean_code = c.split(".")[0]
            else:
                clean_code = c
                yf_code = f"{c}.SS" if c.startswith("6") or c.startswith("9") else f"{c}.SZ"
            name = get_stock_name(clean_code)
            pool.append((yf_code, name, ""))
            logger.info(f"股票池: {yf_code} -> {name}")

    results=[]
    logger.info(f"选股开始，候选 {len(pool)} 支")
    for sym,name,*_ in pool:
        try:
            h=yf.Ticker(sym).history(period="3mo",interval="1d")
            if h.empty or len(h)<30: continue
            close=h["Close"].tolist(); high=h["High"].tolist()
            low=h["Low"].tolist(); vol=h["Volume"].tolist()
            pe=0.0
            try: pe=float(getattr(yf.Ticker(sym).fast_info,"pe_ratio",0) or 0)
            except: pass
            fs=_score_one(close,high,low,vol,pe,weights)
            if fs is None: continue
            tot=_total(fs,weights)
            price=round(close[-1],2)
            chg=round((close[-1]-close[-2])/close[-2]*100,2) if len(close)>=2 else 0.0
            avg_v=sum(vol[-21:-1])/20 if len(vol)>=21 else 1
            vr=round(vol[-1]/avg_v,2) if avg_v else 1.0

            clean_code = sym.split(".")[0]
            stock_name = name if name and name != sym and name != clean_code else get_stock_name(clean_code)
            
            logger.info(f"处理股票: {sym} -> name={name} -> stock_name={stock_name}")

            results.append(StockScore(
                code=clean_code, name=stock_name, price=price,
                change_pct=chg, total_score=tot, factor_scores=fs,
                buy_reason=_reason(fs), risk_tip=_risk(fs),
                pe=pe, volume_ratio=vr
            ))
            time.sleep(0.15)
        except Exception as e:
            logger.debug(f"[{sym}] 失败: {e}")

    results.sort(key=lambda x:x.total_score, reverse=True)
    top=results[:top_n]
    logger.info(f"选股完成：{len(results)} 支有效，推荐 Top-{len(top)}")
    for i, s in enumerate(top[:5], 1):
        logger.info(f"  {i}. {s.name}({s.code}) 评分:{s.total_score:.2f}")
    return top or _demo(top_n)


def _demo(n):
    d=[("600519","贵州茅台",1688,2.3,0.81,"MACD金叉、低估值"),
       ("300750","宁德时代",185.4,3.1,0.76,"放量上涨、KDJ多头"),
       ("002594","比亚迪",235.6,2.8,0.74,"短线强势、中期趋势向上"),
       ("600036","招商银行",35.8,1.9,0.72,"低估值、MACD金叉"),
       ("688981","中芯国际",58.2,4.2,0.70,"放量上涨、半导体强势")]
    return [StockScore(code=c,name=nm,price=p,change_pct=ch,
            total_score=sc,buy_reason=r,risk_tip="风险适中",pe=15.0,volume_ratio=1.2) for c,nm,p,ch,sc,r in d[:n]]
