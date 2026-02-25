#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股财经新闻RSS聚合与邮件推送
每日自动抓取主要财经网站的RSS新闻并发送到邮箱
使用Yahoo Finance API获取A股数据
"""

import sys
sys.path.insert(0, r'E:\ENV\python-packages')

import os
import smtplib
import feedparser
import yfinance as yf
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import time
from functools import wraps
import requests
from stock_names import get_stock_name  # 导入股票名称映射

# RSS源列表 - 全部中文财经新闻源
RSS_FEEDS = {
    # 可从国外访问的中文财经源
    'FT中文网': 'https://www.ftchinese.com/rss/news',
    'FT中文网-经济': 'https://www.ftchinese.com/rss/economy',
    'FT中文网-金融市场': 'https://www.ftchinese.com/rss/markets',

    # 华尔街日报中文版
    '华尔街日报中文-经济': 'https://cn.wsj.com/zh-hans/rss/economy',
    '华尔街日报中文-市场': 'https://cn.wsj.com/zh-hans/rss/markets',

    # RSSHub公共实例（中文源）
    'RSSHub-财联社': 'https://rsshub.app/cls/telegraph',
    'RSSHub-36氪': 'https://rsshub.app/36kr/newsflashes',
    'RSSHub-新浪财经': 'https://rsshub.app/sina/finance',
    'RSSHub-雪球': 'https://rsshub.app/xueqiu/hots',
    'RSSHub-第一财经': 'https://rsshub.app/yicai/brief',
}

# 请求头，模拟浏览器
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# 板块关键词映射
SECTOR_KEYWORDS = {
    '新能源': ['新能源', '光伏', '风电', '储能', '锂电', '电池'],
    '人工智能': ['AI', '人工智能', '大模型', '算力', 'ChatGPT', '芯片'],
    '医药': ['医药', '生物', '疫苗', '医疗', 'CXO', '创新药'],
    '半导体': ['半导体', '芯片', '集成电路', '晶圆', '光刻'],
    '军工': ['军工', '国防', '航空', '航天', '导弹'],
    '消费': ['消费', '白酒', '食品', '零售', '电商'],
    '地产': ['地产', '房地产', '物业', '建筑'],
    '金融': ['银行', '保险', '券商', '证券', '信托'],
    '新基建': ['5G', '数据中心', '云计算', '物联网', '工业互联网'],
    '汽车': ['汽车', '新能源车', '智能驾驶', '自动驾驶'],
}

# 美股 / 港股 / AI 大模型 关键词
US_MARKET_KEYWORDS = [
    '美股',
    '美国股市',
    '纳斯达克',
    '纳指',
    '道琼斯',
    '标普500',
    '标普 500',
    'S&P 500',
    '纽约证交所',
    '纽约证券交易所',
]

HK_MARKET_KEYWORDS = [
    '港股',
    '香港股市',
    '恒生指数',
    '恒指',
    '国企指数',
    '港交所',
    '联交所',
]

AI_MODEL_KEYWORDS = [
    '大模型',
    '人工智能',
    'AI',
    '生成式AI',
    '生成式 AI',
    'ChatGPT',
    '通义千问',
    '千问',
    'GLM',
    'DeepSeek',
    'MiniMax',
    '月之暗面',
    'Ring-2.5',
    'Qwen',
]

# 生成所有A股主板股票代码
# 上海交易所：600000-603999 + .SS
# 深圳交易所：000000-002999 + .SZ
def generate_all_main_board_stocks():
    """生成所有可能的主板股票代码"""
    stocks = []

    # 上海主板：600000-603999
    for prefix in ['600', '601', '603']:
        for i in range(1000):
            code = f"{prefix}{i:03d}.SS"
            stocks.append(code)

    # 深圳主板：000000-002999
    for prefix in ['000', '001', '002']:
        for i in range(1000):
            code = f"{prefix}{i:03d}.SZ"
            stocks.append(code)

    return stocks

SAMPLE_STOCKS = generate_all_main_board_stocks()  # 约6000只股票代码

def retry_on_failure(max_retries=3, delay=2):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    print(f"  尝试 {attempt + 1}/{max_retries} 失败: {str(e)[:50]}, {delay}秒后重试...")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

def fetch_rss_news():
    """抓取所有RSS源的新闻（带重试和超时）"""
    all_news = []
    success_count = 0
    fail_count = 0

    for source_name, feed_url in RSS_FEEDS.items():
        try:
            print(f"正在抓取: {source_name}")

            # 设置User-Agent
            feedparser.USER_AGENT = USER_AGENT

            # 使用重试机制抓取（feedparser不支持timeout参数，移除）
            @retry_on_failure(max_retries=2, delay=1)
            def fetch_feed():
                return feedparser.parse(feed_url)

            feed = fetch_feed()

            if not feed or not hasattr(feed, 'entries') or not feed.entries:
                print(f"  ⚠️ {source_name} 返回空数据")
                fail_count += 1
                continue

            # 获取前5条新闻
            for entry in feed.entries[:5]:
                news_item = {
                    'source': source_name,
                    'title': entry.get('title', '无标题'),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'summary': entry.get('summary', '')[:200] + '...' if entry.get('summary') else ''
                }
                all_news.append(news_item)

            success_count += 1
            print(f"  ✓ 成功获取 {len(feed.entries[:5])} 条")

            # 避免请求过快
            time.sleep(2)

        except Exception as e:
            print(f"  ✗ 抓取失败: {str(e)[:80]}")
            fail_count += 1
            continue

    print(f"\n抓取统计: 成功 {success_count} 个源, 失败 {fail_count} 个源")
    return all_news

def analyze_hot_sectors(news_list):
    """分析新闻中提到的热门板块"""
    sector_mentions = {sector: [] for sector in SECTOR_KEYWORDS.keys()}

    for news in news_list:
        text = news['title'] + ' ' + news.get('summary', '')

        for sector, keywords in SECTOR_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    sector_mentions[sector].append({
                        'title': news['title'],
                        'source': news['source'],
                        'link': news['link']
                    })
                    break  # 找到一个关键词就够了

    # 按提及次数排序，取前5个
    hot_sectors = sorted(
        [(sector, items) for sector, items in sector_mentions.items() if items],
        key=lambda x: len(x[1]),
        reverse=True
    )[:5]

    return hot_sectors


def analyze_global_and_ai_news(news_list, max_items_per_section=5):
    """从新闻中抽取美股/港股大事件与AI大模型动态"""
    us_events = []
    hk_events = []
    ai_events = []

    seen_us = set()
    seen_hk = set()
    seen_ai = set()

    for news in news_list:
        text = (news.get('title', '') or '') + ' ' + (news.get('summary', '') or '')

        # 美股 / 美国市场
        if len(us_events) < max_items_per_section:
            if any(keyword in text for keyword in US_MARKET_KEYWORDS):
                key = news.get('title', '') + news.get('link', '')
                if key not in seen_us:
                    us_events.append(news)
                    seen_us.add(key)

        # 港股 / 香港市场
        if len(hk_events) < max_items_per_section:
            if any(keyword in text for keyword in HK_MARKET_KEYWORDS):
                key = news.get('title', '') + news.get('link', '')
                if key not in seen_hk:
                    hk_events.append(news)
                    seen_hk.add(key)

        # AI 大模型
        if len(ai_events) < max_items_per_section:
            if any(keyword in text for keyword in AI_MODEL_KEYWORDS):
                key = news.get('title', '') + news.get('link', '')
                if key not in seen_ai:
                    ai_events.append(news)
                    seen_ai.add(key)

    return us_events, hk_events, ai_events

def get_hot_stocks(hot_sector_names):
    """使用Yahoo Finance获取A股优质股票 - 分析全部主板股票"""
    try:
        print("正在从Yahoo Finance获取A股数据...")
        print(f"  准备分析全部 {len(SAMPLE_STOCKS)} 只主板股票")

        stocks_data = []
        success_count = 0
        fail_count = 0

        # 分析全部股票（不再随机抽取）
        for i, symbol in enumerate(SAMPLE_STOCKS):
            try:
                if i % 100 == 0:
                    print(f"  进度: {i}/{len(SAMPLE_STOCKS)}")

                # 获取股票信息
                ticker = yf.Ticker(symbol)

                # 获取最近2天的历史数据
                hist = ticker.history(period='2d')

                if hist.empty or len(hist) < 2:
                    fail_count += 1
                    continue

                # 获取今日和昨日数据
                today = hist.iloc[-1]
                yesterday = hist.iloc[-2]

                # 计算涨跌幅
                change_pct = ((today['Close'] - yesterday['Close']) / yesterday['Close']) * 100

                # 只保留上涨的股票
                if change_pct <= 0:
                    continue

                # 使用映射表获取中文名称
                stock_name = get_stock_name(symbol)

                # 计算成交量变化（活跃度）
                volume_change = ((today['Volume'] - yesterday['Volume']) / yesterday['Volume']) * 100 if yesterday['Volume'] > 0 else 0

                # 计算振幅
                amplitude = ((today['High'] - today['Low']) / yesterday['Close']) * 100

                # 换手率估算（成交量/流通股本，简化处理）
                info = ticker.info
                shares_outstanding = info.get('sharesOutstanding', 0)
                turnover = (today['Volume'] / shares_outstanding * 100) if shares_outstanding > 0 else 0

                # 新的评分系统（总分100分）
                # 热度占比很大，成交量和趋势小一点

                # 1. 涨幅得分 (0-25分)
                change_score = min(change_pct * 2.5, 25)

                # 2. 成交量得分 (0-15分) - 降低权重
                volume_score = min(abs(volume_change) / 10, 15)

                # 3. 趋势得分 (0-10分) - 降低权重
                trend_score = min(amplitude * 1, 10)

                # 4. 板块热度得分 (0-50分) - 大幅提高权重
                sector_score = 0
                for sector_name in hot_sector_names:
                    for keyword in SECTOR_KEYWORDS.get(sector_name, []):
                        if keyword in stock_name:
                            sector_score = 50  # 热门板块给满分
                            break
                    if sector_score > 0:
                        break

                # 如果不在热门板块，但涨幅很高，也给一些热度分
                if sector_score == 0 and change_pct > 5:
                    sector_score = 20  # 涨幅高的股票也有一定热度

                # 总分（满分100分）
                total_score = change_score + volume_score + trend_score + sector_score

                # 收集所有上涨的股票（降低阈值到30分，因为热度权重提高了）
                if total_score >= 30:
                    stocks_data.append({
                        'code': symbol.split('.')[0],
                        'name': stock_name,
                        'price': float(today['Close']),
                        'change_pct': round(change_pct, 2),
                        'turnover': round(turnover, 2),
                        'amplitude': round(amplitude, 2),
                        'volume': int(today['Volume']),
                        'market_cap': info.get('marketCap', 0),
                        'score': round(total_score, 1),
                        'change_score': round(change_score, 1),
                        'volume_score': round(volume_score, 1),
                        'trend_score': round(trend_score, 1),
                        'sector_score': round(sector_score, 1)
                    })

                success_count += 1

                # 加快请求速度（全部股票需要更快）
                time.sleep(0.02)

            except Exception as e:
                fail_count += 1
                continue

        print(f"\n  数据获取统计: 成功 {success_count} 只, 失败 {fail_count} 只")
        print(f"  找到 {len(stocks_data)} 只评分≥30的股票")

        # 按综合得分排序
        sorted_stocks = sorted(stocks_data, key=lambda x: x['score'], reverse=True)

        # 返回前10只最优质的股票
        top_stocks = sorted_stocks[:10]

        print(f"  返回前 {len(top_stocks)} 只优质股票")
        return top_stocks

    except Exception as e:
        print(f"⚠️ 获取股票数据失败: {str(e)[:100]}")
        return []

def format_email_content(news_list, hot_sectors, hot_stocks, us_events, hk_events, ai_events):
    """格式化邮件内容为HTML"""
    today = datetime.now().strftime('%Y年%m月%d日')

    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                       color: white; padding: 20px; text-align: center; }}
            .section-title {{ font-size: 20px; font-weight: bold; color: #667eea;
                             margin: 25px 0 15px 0; padding-bottom: 10px;
                             border-bottom: 2px solid #667eea; }}
            .hot-sectors {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 15px 0; }}
            .sector-tag {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                          color: white; padding: 10px 15px; border-radius: 20px;
                          font-weight: bold; display: inline-block; }}
            .sector-count {{ background: rgba(255,255,255,0.3); padding: 2px 8px;
                            border-radius: 10px; margin-left: 5px; }}
            .sector-news {{ background: #fff3e0; padding: 10px; margin: 10px 0;
                           border-left: 4px solid #ff9800; border-radius: 4px; }}
            .sector-news-title {{ font-size: 14px; color: #333; margin: 5px 0; }}
            .stock-table {{ width: 100%; border-collapse: collapse; margin: 15px 0;
                           background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .stock-table th {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                              color: white; padding: 12px; text-align: left; font-size: 14px; }}
            .stock-table td {{ padding: 10px; border-bottom: 1px solid #eee; font-size: 13px; }}
            .stock-table tr:hover {{ background: #f5f5f5; }}
            .stock-name {{ font-weight: bold; color: #333; }}
            .stock-code {{ color: #999; font-size: 12px; }}
            .price-up {{ color: #f44336; font-weight: bold; }}
            .score-badge {{ background: #4caf50; color: white; padding: 3px 8px;
                           border-radius: 12px; font-size: 12px; font-weight: bold; }}
            .score-detail {{ font-size: 11px; color: #666; margin-top: 3px; }}
            .news-item {{ border-left: 4px solid #667eea; padding: 15px;
                         margin: 15px 0; background: #f9f9f9; }}
            .source {{ color: #667eea; font-weight: bold; font-size: 14px; }}
            .title {{ font-size: 16px; font-weight: bold; margin: 8px 0; }}
            .summary {{ color: #666; font-size: 14px; margin: 8px 0; }}
            .link {{ color: #764ba2; text-decoration: none; }}
            .footer {{ text-align: center; color: #999; padding: 20px;
                      border-top: 1px solid #ddd; margin-top: 30px; }}
            .warning-box {{ background: #fff3cd; border-left: 4px solid #ffc107;
                           padding: 15px; margin: 15px 0; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📈 A股财经日报</h1>
            <p>{today}</p>
        </div>
        <div style="padding: 20px;">
    """

    # 全球市场 & AI 大模型部分（无论是否有事件，固定展示一个版块，便于你对比）
    html_content += '<div class="section-title">🌍 美股 / 港股大事件 & AI 大模型动态</div>'

    has_any_event = bool(us_events or hk_events or ai_events)

    # 美股
    if us_events:
        html_content += '<div style="margin: 10px 0 5px 0; font-weight: bold;">🌎 美股 / 全球市场：</div>'
        for item in us_events:
            html_content += f"""
            <div class="news-item">
                <div class="source">📰 {item.get('source', '')}</div>
                <div class="title">{item.get('title', '')}</div>
                <div class="summary">{item.get('summary', '')}</div>
                <a href="{item.get('link', '')}" class="link">查看详情 →</a>
            </div>
            """

    # 港股
    if hk_events:
        html_content += '<div style="margin: 15px 0 5px 0; font-weight: bold;">🌏 港股市场：</div>'
        for item in hk_events:
            html_content += f"""
            <div class="news-item">
                <div class="source">📰 {item.get('source', '')}</div>
                <div class="title">{item.get('title', '')}</div>
                <div class="summary">{item.get('summary', '')}</div>
                <a href="{item.get('link', '')}" class="link">查看详情 →</a>
            </div>
            """

    # AI 大模型
    if ai_events:
        html_content += '<div style="margin: 15px 0 5px 0; font-weight: bold;">🤖 AI 大模型最新动态：</div>'
        for item in ai_events:
            html_content += f"""
            <div class="news-item">
                <div class="source">📰 {item.get('source', '')}</div>
                <div class="title">{item.get('title', '')}</div>
                <div class="summary">{item.get('summary', '')}</div>
                <a href="{item.get('link', '')}" class="link">查看详情 →</a>
            </div>
            """

    # 如果当天 RSS 里没有明显的美股/港股/AI 相关新闻，给出提示文字，避免你误以为代码没生效
    if not has_any_event:
        html_content += """
        <div class="news-item">
            <div class="summary">
                今日从当前RSS新闻源中未检测到明确标注的美股、港股或AI大模型相关重大新闻。
                你可以参考下方的「今日财经要闻」和「热门板块」获取整体市场信息。
            </div>
        </div>
        """

    # 优质股票推荐部分
    if hot_stocks:
        html_content += '<div class="section-title">⭐ 综合评分优质股票（主板）</div>'
        html_content += '''
        <div class="warning-box">
            <strong>⚠️ 评分说明：</strong>综合考虑涨幅(30%)、成交量(25%)、趋势(20%)、板块热度(25%)四个维度。
            仅供参考，不构成投资建议！
        </div>
        <table class="stock-table">
            <tr>
                <th>股票</th>
                <th>最新价</th>
                <th>涨幅</th>
                <th>换手率</th>
                <th>综合评分</th>
            </tr>
        '''
        for stock in hot_stocks:
            html_content += f'''
            <tr>
                <td>
                    <div class="stock-name">{stock['name']}</div>
                    <div class="stock-code">{stock['code']}</div>
                </td>
                <td class="price-up">¥{stock['price']:.2f}</td>
                <td class="price-up">+{stock['change_pct']:.2f}%</td>
                <td>{stock['turnover']:.2f}%</td>
                <td>
                    <span class="score-badge">{stock['score']}分</span>
                    <div class="score-detail">
                        涨幅:{stock['change_score']} 量:{stock['volume_score']}
                        势:{stock['trend_score']} 板:{stock['sector_score']}
                    </div>
                </td>
            </tr>
            '''
        html_content += '</table>'

    # 热门板块部分
    if hot_sectors:
        html_content += '<div class="section-title">🔥 今日热门板块</div>'
        html_content += '<div class="hot-sectors">'
        for sector, items in hot_sectors:
            html_content += f'''
            <div class="sector-tag">
                {sector} <span class="sector-count">{len(items)}条</span>
            </div>
            '''
        html_content += '</div>'

        # 显示每个板块的相关新闻
        for sector, items in hot_sectors:
            html_content += f'<div style="margin: 20px 0;"><strong>📊 {sector}板块相关：</strong></div>'
            for item in items[:3]:  # 每个板块最多显示3条
                html_content += f'''
                <div class="sector-news">
                    <div class="sector-news-title">• {item['title']}</div>
                    <div style="font-size: 12px; color: #999; margin-top: 5px;">
                        来源: {item['source']} | <a href="{item['link']}" style="color: #ff9800;">查看详情</a>
                    </div>
                </div>
                '''

    # 全部新闻部分
    html_content += '<div class="section-title">📰 今日财经要闻</div>'

    if not news_list:
        html_content += "<p>今日暂无新闻更新</p>"
    else:
        for news in news_list:
            html_content += f"""
            <div class="news-item">
                <div class="source">📰 {news['source']}</div>
                <div class="title">{news['title']}</div>
                <div class="summary">{news['summary']}</div>
                <a href="{news['link']}" class="link">阅读全文 →</a>
            </div>
            """

    html_content += """
        </div>
        <div class="footer">
            <p>本邮件由GitHub Actions自动发送</p>
            <p>⚠️ 本邮件仅供信息参考，不构成投资建议</p>
            <p style="font-size: 12px; color: #ccc; margin-top: 10px;">
                股票评分基于多维度综合分析，历史表现不代表未来收益<br>
                投资有风险，入市需谨慎
            </p>
        </div>
    </body>
    </html>
    """

    return html_content

def send_email(content, recipient_email, smtp_password):
    """通过QQ邮箱SMTP发送邮件"""
    sender_email = recipient_email  # 发件人和收件人相同

    # 创建邮件
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'📊 A股财经日报 - {datetime.now().strftime("%Y-%m-%d")}'
    msg['From'] = sender_email
    msg['To'] = recipient_email

    # 添加HTML内容
    html_part = MIMEText(content, 'html', 'utf-8')
    msg.attach(html_part)

    try:
        # 连接QQ邮箱SMTP服务器
        print("正在连接SMTP服务器...")
        server = smtplib.SMTP('smtp.qq.com', 587)
        server.starttls()

        print("正在登录...")
        server.login(sender_email, smtp_password)

        print("正在发送邮件...")
        server.send_message(msg)
        server.quit()

        print(f"✅ 邮件发送成功！发送到: {recipient_email}")
        return True

    except Exception as e:
        print(f"❌ 邮件发送失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("A股财经新闻RSS聚合系统")
    print("=" * 50)

    # 从环境变量获取配置
    recipient_email = os.getenv('QQ_EMAIL')
    smtp_password = os.getenv('QQ_SMTP_PASSWORD')

    if not recipient_email or not smtp_password:
        print("❌ 错误: 未设置环境变量 QQ_EMAIL 或 QQ_SMTP_PASSWORD")
        return

    print(f"\n收件人: {recipient_email}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 1. 抓取新闻
    print("📡 开始抓取RSS新闻...")
    news_list = fetch_rss_news()
    print(f"✅ 成功抓取 {len(news_list)} 条新闻\n")

    # 2. 分析热门板块
    print("🔥 正在分析热门板块...")
    hot_sectors = analyze_hot_sectors(news_list)
    hot_sector_names = [sector for sector, _ in hot_sectors]
    print(f"✅ 发现 {len(hot_sectors)} 个热门板块\n")

    # 3. 提取美股 / 港股 / AI 大模型相关的大事件
    print("🌍 正在分析美股、港股与AI大模型相关新闻...")
    us_events, hk_events, ai_events = analyze_global_and_ai_news(news_list)
    print(f"✅ 美股事件 {len(us_events)} 条，港股事件 {len(hk_events)} 条，AI大模型 {len(ai_events)} 条\n")

    # 4. 获取综合评分高的股票
    print("📊 正在分析优质股票...")
    hot_stocks = get_hot_stocks(hot_sector_names)
    print(f"✅ 筛选出 {len(hot_stocks)} 只优质股票\n")

    # 5. 格式化邮件内容
    print("📝 正在格式化邮件内容...")
    email_content = format_email_content(
        news_list,
        hot_sectors,
        hot_stocks,
        us_events,
        hk_events,
        ai_events,
    )

    # 6. 发送邮件
    print("📧 正在发送邮件...")
    success = send_email(email_content, recipient_email, smtp_password)

    if success:
        print("\n🎉 任务完成！")
    else:
        print("\n⚠️ 任务完成但邮件发送失败")

    print("=" * 50)

if __name__ == '__main__':
    main()
