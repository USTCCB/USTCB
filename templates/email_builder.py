"""
templates/email_builder.py
生成精美 HTML 日报邮件 - 简化版
"""

from datetime import datetime
from typing import List, Dict, Any

from news.aggregator import NewsItem
from news.market_hot import SectorInfo, StockHotInfo, IndexSnapshot
from stock_selectors.multi_factor import StockScore


def _color(val: float) -> str:
    if val > 0: return "#e84040"
    elif val < 0: return "#00b050"
    return "#888888"


def _sign(val: float) -> str:
    return f"+{val:.2f}%" if val > 0 else f"{val:.2f}%"


def _score_bar(score: float) -> str:
    pct = int(score * 100)
    color = "#e84040" if score > 0.7 else ("#f5a623" if score > 0.5 else "#4a90d9")
    return f'<span style="color:{color};font-weight:bold;">{pct}分</span>'


def _section_market_overview(indices: Dict[str, IndexSnapshot]) -> str:
    if not indices: return ""
    rows = ""
    for name in ["上证指数", "深证成指", "创业板指", "沪深300", "科创50", "恒生指数", "道琼斯", "纳斯达克", "标普500"]:
        info = indices.get(name)
        if not info: continue
        c = _color(info.change_pct)
        rows += f'<tr><td>{name}</td><td>{info.price:,.2f}</td><td style="color:{c};">{_sign(info.change_pct)}</td></tr>'
    return f'<div class="section"><h2>📊 全球主要指数</h2><table><thead><tr><th>指数</th><th>最新价</th><th>涨跌幅</th></tr></thead><tbody>{rows}</tbody></table></div>'


def _section_news(category: str, items: List[NewsItem], icon: str) -> str:
    if not items: return ""
    rows = "".join([f'<div class="news-item"><a href="{i.link}">{i.title}</a><span>{i.source}</span></div>' for i in items[:12]])
    return f'<div class="section"><h2>{icon} {category}</h2>{rows}</div>'


def _section_hot_sectors(sectors: List[SectorInfo]) -> str:
    if not sectors: return ""
    cards = "".join([f'<div class="sector-card"><div>{s.name}</div><div style="color:{_color(s.change_pct)};">{_sign(s.change_pct)}</div></div>' for s in sectors])
    return f'<div class="section"><h2>🔥 热门板块</h2><div class="sector-grid">{cards}</div></div>'


def _section_hot_stocks(stocks: List[StockHotInfo]) -> str:
    if not stocks: return ""
    rows = "".join([f'<tr><td>{s.code}</td><td>{s.name}</td><td>{s.price:.2f}</td><td style="color:{_color(s.change_pct)};">{_sign(s.change_pct)}</td></tr>' for s in stocks])
    return f'<div class="section"><h2>💥 热门股票</h2><table><thead><tr><th>代码</th><th>名称</th><th>价格</th><th>涨跌幅</th></tr></thead><tbody>{rows}</tbody></table></div>'


def _section_top_picks(picks: List[StockScore]) -> str:
    if not picks: return ""
    rows = ""
    for i, s in enumerate(picks, 1):
        medal = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else f"#{i}"
        rows += f'<tr><td>{medal}</td><td>{s.name}<br>{s.code}</td><td>¥{s.price:.2f}<br>{_sign(s.change_pct)}</td><td>{_score_bar(s.total_score)}</td><td>{s.buy_reason}</td><td>{s.risk_tip}</td></tr>'
    return f'<div class="section"><h2>🎯 AI量化选股 Top {len(picks)}</h2><table><thead><tr><th>排名</th><th>股票</th><th>价格</th><th>评分</th><th>信号</th><th>风险</th></tr></thead><tbody>{rows}</tbody></table></div>'


CSS = '<style>body{font-family:sans-serif;background:#f0f2f5;margin:0;padding:0}.container{max-width:780px;margin:0 auto;background:#fff}.header{background:#1a1a2e;color:#fff;padding:32px 24px;text-align:center}.section{padding:20px 24px;border-bottom:1px solid #f0f0f0}.news-item{padding:10px 0}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:7px 10px;border-bottom:1px solid #f0f0f0}.sector-grid{display:flex;flex-wrap:wrap;gap:12px}.sector-card{background:#f9f9f9;border-radius:8px;padding:12px;min-width:120px}.footer{background:#1a1a2e;color:#666;text-align:center;padding:16px}</style>'


def build_html_email(date_str: str, indices: Dict[str, IndexSnapshot], news_by_category: Dict[str, List[NewsItem]], hot_sectors: List[SectorInfo], hot_stocks: List[StockHotInfo], top_picks: List[StockScore], north_flow: Dict[str, Any]) -> str:
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{CSS}</head>
<body>
<div class="container">
  <div class="header"><h1>📈 全球财经 &amp; AI资讯日报</h1><p>{now}</p></div>
  {_section_market_overview(indices)}
  {_section_top_picks(top_picks)}
  {_section_hot_sectors(hot_sectors)}
  {_section_hot_stocks(hot_stocks)}
  {_section_news("A股财经要闻", news_by_category.get("A股财经", []), "🇨🇳")}
  {_section_news("美股要闻", news_by_category.get("美股要闻", []), "🇺🇸")}
  {_section_news("港股要闻", news_by_category.get("港股要闻", []), "🇭🇰")}
  {_section_news("AI大模型动态", news_by_category.get("AI大模型", []), "🤖")}
  <div class="footer"><p>本邮件由 USTCB 财经日报机器人自动生成 · {now}</p></div>
</div>
</body>
</html>'''
