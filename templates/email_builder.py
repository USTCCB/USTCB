"""
templates/email_builder.py
生成精美 HTML 日报邮件
"""

from datetime import datetime
from typing import List, Dict, Any

from news.aggregator import NewsItem
from news.market_hot import SectorInfo, StockHotInfo
from stock_selectors.multi_factor import StockScore


# ─── 颜色辅助 ─────────────────────────────────────────────────

def _color(val: float) -> str:
    """涨红跌绿"""
    if val > 0:
        return "#e84040"
    elif val < 0:
        return "#00b050"
    return "#888888"


def _sign(val: float) -> str:
    return f"+{val:.2f}%" if val > 0 else f"{val:.2f}%"


def _score_bar(score: float) -> str:
    """可视化评分条"""
    pct = int(score * 100)
    color = "#e84040" if score > 0.7 else ("#f5a623" if score > 0.5 else "#4a90d9")
    return (
        f'<div style="display:inline-block;width:80px;height:8px;'
        f'background:#eee;border-radius:4px;vertical-align:middle;">'
        f'<div style="width:{pct}%;height:100%;background:{color};border-radius:4px;"></div>'
        f'</div> <span style="color:{color};font-weight:bold;">{pct}</span>'
    )


# ─── 各板块 HTML 生成 ──────────────────────────────────────────

def _section_market_overview(indices: Dict[str, Dict]) -> str:
    if not indices:
        return ""
    rows = ""
    order = ["上证指数", "深证成指", "创业板指", "沪深300", "科创50", "恒生指数", "道琼斯", "纳斯达克", "标普500"]
    for name in order:
        info = indices.get(name)
        if not info:
            continue
        c = _color(info["change_pct"])
        rows += (
            f'<tr>'
            f'<td style="padding:6px 12px;">{name}</td>'
            f'<td style="padding:6px 12px;font-weight:bold;">{info["price"]:,.2f}</td>'
            f'<td style="padding:6px 12px;color:{c};font-weight:bold;">{_sign(info["change_pct"])}</td>'
            f'</tr>'
        )
    return f"""
<div class="section">
  <h2>📊 全球主要指数</h2>
  <table style="width:100%;border-collapse:collapse;font-size:14px;">
    <thead><tr style="background:#f5f5f5;">
      <th style="padding:8px 12px;text-align:left;">指数</th>
      <th style="padding:8px 12px;text-align:left;">最新价</th>
      <th style="padding:8px 12px;text-align:left;">涨跌幅</th>
    </tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>"""


def _section_news(category: str, items: List[NewsItem], icon: str) -> str:
    if not items:
        return ""
    rows = ""
    for item in items[:12]:
        rows += (
            f'<div class="news-item">'
            f'  <a href="{item.link}" target="_blank" class="news-title">{item.title}</a>'
            f'  <span class="news-meta">{item.source} {item.published}</span>'
            f'  {"<p class=news-summary>" + item.summary[:120] + "...</p>" if item.summary else ""}'
            f'</div>'
        )
    return f"""
<div class="section">
  <h2>{icon} {category}</h2>
  {rows}
</div>"""


def _section_hot_sectors(sectors: List[SectorInfo]) -> str:
    if not sectors:
        return ""
    cards = ""
    for s in sectors:
        c = _color(s.change_pct)
        cards += (
            f'<div class="sector-card">'
            f'  <div class="sector-name">{s.name}</div>'
            f'  <div class="sector-chg" style="color:{c};">{_sign(s.change_pct)}</div>'
            f'  <div class="sector-lead">领涨：{s.leading_stock} '
            f'    <span style="color:{_color(s.leading_change)};">{_sign(s.leading_change)}</span>'
            f'  </div>'
            f'</div>'
        )
    return f"""
<div class="section">
  <h2>🔥 热门板块（今日涨幅榜）</h2>
  <div class="sector-grid">{cards}</div>
</div>"""


def _section_hot_stocks(stocks: List[StockHotInfo]) -> str:
    if not stocks:
        return ""
    rows = ""
    for s in stocks:
        c = _color(s.change_pct)
        rows += (
            f'<tr>'
            f'<td>{s.code}</td>'
            f'<td style="font-weight:bold;">{s.name}</td>'
            f'<td>{s.price:.2f}</td>'
            f'<td style="color:{c};font-weight:bold;">{_sign(s.change_pct)}</td>'
            f'<td>{s.volume_ratio:.2f}x</td>'
            f'<td>{s.turnover:.1f}%</td>'
            f'<td style="color:#888;font-size:12px;">{s.concept[:10]}</td>'
            f'</tr>'
        )
    return f"""
<div class="section">
  <h2>💥 热门股票（今日活跃榜）</h2>
  <table style="width:100%;border-collapse:collapse;font-size:13px;">
    <thead><tr style="background:#f5f5f5;">
      <th>代码</th><th>名称</th><th>价格</th><th>涨跌幅</th><th>量比</th><th>换手率</th><th>概念</th>
    </tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>"""


def _section_top_picks(picks: List[StockScore]) -> str:
    if not picks:
        return ""
    rows = ""
    for i, s in enumerate(picks, 1):
        medal = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else f"#{i}"
        c = _color(s.change_pct)
        north_txt = f"<span style='color:#e84040;'>↑{s.north_net/1e4:.1f}亿</span>" if s.north_net > 0 else \
                    (f"<span style='color:#00b050;'>↓{abs(s.north_net)/1e4:.1f}亿</span>" if s.north_net < 0 else "—")
        rows += f"""
        <tr style="{'background:#fffbf0;' if i <= 3 else ''}">
          <td style="font-size:18px;text-align:center;">{medal}</td>
          <td><b>{s.name}</b><br><span style="color:#888;font-size:11px;">{s.code}</span></td>
          <td>¥{s.price:.2f}<br><span style="color:{c};font-size:11px;">{_sign(s.change_pct)}</span></td>
          <td>{_score_bar(s.total_score)}</td>
          <td style="font-size:11px;color:#555;">
            PE: {s.pe:.1f}<br>PB: {s.pb:.1f}<br>ROE: {s.roe:.1f}%
          </td>
          <td style="font-size:11px;">北向: {north_txt}<br>量比: {s.volume_ratio:.1f}x</td>
          <td style="color:#2a6ebb;font-size:11px;">{s.buy_reason}</td>
          <td style="color:#e84040;font-size:10px;">{s.risk_tip}</td>
        </tr>"""
    return f"""
<div class="section highlight-section">
  <h2>🎯 AI多因子量化选股（今日推荐 A股 Top {len(picks)}）</h2>
  <p style="color:#888;font-size:12px;">⚠️ 基于技术面+资金面+估值+基本面 12因子模型，仅供参考，不构成投资建议。股市有风险，入市需谨慎。</p>
  <table style="width:100%;border-collapse:collapse;font-size:13px;">
    <thead>
      <tr style="background:#fff3cd;">
        <th>排名</th><th>股票</th><th>价格/涨幅</th><th>综合评分</th><th>估值面</th><th>资金面</th><th>买入信号</th><th>风险提示</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
</div>"""


def _section_north_fund(flow: Dict[str, Any]) -> str:
    if flow.get("status") != "ok":
        return ""
    total = flow["total"]
    sh = flow["sh"]
    sz = flow["sz"]
    c = _color(total)
    return f"""
<div class="section">
  <h2>🧲 北向资金（今日）</h2>
  <div style="display:flex;gap:20px;flex-wrap:wrap;">
    <div class="fund-box">
      <div class="fund-label">沪股通</div>
      <div class="fund-val" style="color:{_color(sh)};">{sh:+.2f} 亿</div>
    </div>
    <div class="fund-box">
      <div class="fund-label">深股通</div>
      <div class="fund-val" style="color:{_color(sz)};">{sz:+.2f} 亿</div>
    </div>
    <div class="fund-box" style="border:2px solid {c};">
      <div class="fund-label">合计净流入</div>
      <div class="fund-val" style="color:{c};font-size:24px;">{total:+.2f} 亿</div>
    </div>
  </div>
</div>"""


# ─── 完整邮件 HTML ─────────────────────────────────────────────

CSS = """
<style>
  body { font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; background:#f0f2f5; margin:0; padding:0; }
  .container { max-width:780px; margin:0 auto; background:#fff; }
  .header { background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);
            color:#fff; padding:32px 24px; text-align:center; }
  .header h1 { margin:0; font-size:26px; letter-spacing:2px; }
  .header p  { margin:8px 0 0; color:#aac; font-size:13px; }
  .section { padding:20px 24px; border-bottom:1px solid #f0f0f0; }
  .section h2 { font-size:17px; margin:0 0 14px; color:#1a1a2e; }
  .news-item { padding:10px 0; border-bottom:1px dashed #eee; }
  .news-title { color:#1a73e8; text-decoration:none; font-size:14px; font-weight:600; line-height:1.5; }
  .news-title:hover { text-decoration:underline; }
  .news-meta { font-size:11px; color:#aaa; margin-left:8px; }
  .news-summary { font-size:12px; color:#666; margin:4px 0 0; line-height:1.6; }
  .sector-grid { display:flex; flex-wrap:wrap; gap:12px; }
  .sector-card { background:#f9f9f9; border-radius:8px; padding:12px 16px;
                 min-width:120px; border:1px solid #eee; }
  .sector-name { font-size:13px; font-weight:bold; color:#333; }
  .sector-chg  { font-size:20px; font-weight:bold; margin:4px 0; }
  .sector-lead { font-size:11px; color:#888; }
  table th, table td { text-align:left; padding:7px 10px; border-bottom:1px solid #f0f0f0; }
  table th { font-size:12px; color:#666; font-weight:600; }
  .highlight-section { background:linear-gradient(180deg,#fffef5 0%,#fff 100%); }
  .fund-box { background:#f9f9f9; border-radius:8px; padding:14px 20px;
              text-align:center; border:1px solid #eee; min-width:120px; }
  .fund-label { font-size:12px; color:#888; }
  .fund-val   { font-size:20px; font-weight:bold; margin-top:6px; }
  .footer { background:#1a1a2e; color:#666; text-align:center;
            padding:16px; font-size:11px; }
  .footer a { color:#4a90d9; text-decoration:none; }
</style>
"""


def build_html_email(
    date_str: str,
    indices: Dict[str, Dict],
    news_by_category: Dict[str, List[NewsItem]],
    hot_sectors: List[SectorInfo],
    hot_stocks: List[StockHotInfo],
    top_picks: List[StockScore],
    north_flow: Dict[str, Any],
) -> str:
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    
    body = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{CSS}</head>
<body>
<div class="container">

  <div class="header">
    <h1>📈 全球财经 &amp; AI资讯日报</h1>
    <p>{now} &nbsp;|&nbsp; A股 · 美股 · 港股 · AI大模型 · 量化选股</p>
  </div>

  {_section_market_overview(indices)}
  {_section_north_fund(north_flow)}
  {_section_top_picks(top_picks)}
  {_section_hot_sectors(hot_sectors)}
  {_section_hot_stocks(hot_stocks)}
  {_section_news("A股财经要闻", news_by_category.get("A股财经", []), "🇨🇳")}
  {_section_news("美股要闻", news_by_category.get("美股要闻", []), "🇺🇸")}
  {_section_news("港股要闻", news_by_category.get("港股要闻", []), "🇭🇰")}
  {_section_news("AI大模型动态", news_by_category.get("AI大模型", []), "🤖")}

  <div class="footer">
    <p>本邮件由 <b>USTCB 财经日报机器人</b> 自动生成 · {now}</p>
    <p>⚠️ 内容仅供参考，不构成投资建议。投资有风险，入市需谨慎。</p>
  </div>
</div>
</body>
</html>"""
    return body
