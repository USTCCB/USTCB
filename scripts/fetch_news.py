#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全球财经与AI前沿资讯聚合 & A股量化强力选股
每日自动抓取主要中文/英文财经与科技RSS源，并利用多因子算法挑选A股标的
"""

import os
import smtplib
import warnings
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import wraps
import time

import feedparser
import pandas as pd
import requests
import yfinance as yf

from stock_names import get_stock_name

# 忽略 yfinance 的部分告警（如多线程相关）
warnings.filterwarnings("ignore")


# 升级版 RSS 源：覆盖 AI 大模型、美股/全球宏观、A股/港股与国内财经
# 每个条目：名称 -> (RSS 地址, 所属分类)
RSS_FEEDS = {
    # === AI 与大模型前沿（中文科技媒体） ===
    '机器之心(AI前沿)': ('https://rsshub.app/jiqizhixin/daily', 'AI大模型'),
    '36氪(AI资讯)': ('https://rsshub.app/36kr/search/articles/AI', 'AI大模型'),
    '极客公园(科技前沿)': ('https://rsshub.app/geekpark/breakingnews', 'AI大模型'),

    # === 美股与全球宏观（中英文混合） ===
    '华尔街见闻(全球)': ('https://rsshub.app/wallstreetcn/news/global', '美股与全球'),
    '华尔街日报(美股)': ('https://cn.wsj.com/zh-hans/rss/markets', '美股与全球'),
    'FT中文网(全球市场)': ('https://www.ftchinese.com/rss/markets', '美股与全球'),
    # Reuters - US Markets（英文，美股与全球市场要闻）
    'Reuters-US-Markets': ('http://feeds.reuters.com/reuters/USmarkets', '美股与全球'),
    # Reuters - World News（全球宏观、地缘政治，对市场有影响）
    'Reuters-World-News': ('http://feeds.reuters.com/reuters/worldNews', '美股与全球'),

    # === AI / 科技（英文科技媒体） ===
    'TechCrunch-AI': ('https://techcrunch.com/tag/artificial-intelligence/feed/', 'AI大模型'),
    'TechCrunch-Main': ('https://techcrunch.com/feed/', 'AI大模型'),

    # === 港股 / 亚洲商业 ===
    'SCMP-Business': ('https://www.scmp.com/rss/91/feed', '美股与全球'),

    # === A股、港股与国内财经（中文） ===
    '财联社(A股电报)': ('https://rsshub.app/cls/telegraph', 'A股与国内'),
    '雪球(全网热帖)': ('https://rsshub.app/xueqiu/hots', 'A股与国内'),
    '格隆汇(港股/A股)': ('https://rsshub.app/gelonghui/live', 'A股与国内'),
}


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


# 需要默认进行英文->中文翻译的源
ENGLISH_SOURCES = {
    "Reuters-US-Markets",
    "Reuters-World-News",
    "TechCrunch-AI",
    "TechCrunch-Main",
    "SCMP-Business",
}


# 热门板块关键词（强调 AI 大模型、出海等当下热点）
SECTOR_KEYWORDS = {
    "AI与大模型": ["AI", "人工智能", "大模型", "算力", "ChatGPT", "Sora", "芯片", "数据", "算法", "服务器", "英伟达"],
    "新能源与储能": ["新能源", "光伏", "风电", "储能", "固态电池", "锂电"],
    "生物医药": ["医药", "生物", "医疗", "创新药", "CXO", "减肥药"],
    "半导体自主可控": ["半导体", "集成电路", "晶圆", "光刻", "存储"],
    "国防军工": ["军工", "国防", "航空", "航天", "卫星", "大飞机"],
    "大消费与文旅": ["消费", "白酒", "文旅", "零售", "家电", "出海"],
    "金融与高股息": ["银行", "保险", "券商", "高股息", "中字头", "红利"],
    "智能汽车产业链": ["汽车", "智能驾驶", "自动驾驶", "华为汽车", "汽配"],
}


def generate_all_main_board_stocks() -> list[str]:
    """生成所有主板股票代码（沪深主板 600/601/603/000/001/002 段）"""
    stocks: list[str] = []
    for prefix in ["600", "601", "603"]:
        for i in range(1000):
            stocks.append(f"{prefix}{i:03d}.SS")
    for prefix in ["000", "001", "002"]:
        for i in range(1000):
            stocks.append(f"{prefix}{i:03d}.SZ")
    return stocks


SAMPLE_STOCKS = generate_all_main_board_stocks()


def retry_on_failure(max_retries: int = 3, delay: int = 2):
    """简单重试装饰器，用于RSS抓取"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(delay)
            return None

        return wrapper

    return decorator


def translate_text(text: str, target_lang: str = "zh") -> str:
    """
    使用免费/自建的 LibreTranslate 兼容 API 将文本翻译为中文。
    - 默认读取环境变量 TRANSLATE_API_URL（必须），可选 TRANSLATE_API_KEY。
    - 调用失败时直接返回原文，保证邮件正常发送。
    """
    text = (text or "").strip()
    if not text:
        return text

    api_url = os.getenv("TRANSLATE_API_URL")
    if not api_url:
        # 未配置翻译服务时直接返回原文
        return text

    payload = {
        "q": text,
        "source": "auto",
        "target": target_lang,
        "format": "text",
    }
    api_key = os.getenv("TRANSLATE_API_KEY")
    if api_key:
        payload["api_key"] = api_key

    try:
        resp = requests.post(api_url, json=payload, timeout=10)
        if resp.status_code != 200:
            return text
        data = resp.json()
        translated = data.get("translatedText") or data.get("translated_text")
        return translated or text
    except Exception:
        return text


def fetch_rss_news() -> dict[str, list[dict]]:
    """分类抓取RSS源新闻，按“AI大模型 / 美股与全球 / A股与国内”划分"""
    categorized_news: dict[str, list[dict]] = {
        "AI大模型": [],
        "美股与全球": [],
        "A股与国内": [],
    }
    success_count = 0

    for source_name, (feed_url, category) in RSS_FEEDS.items():
        try:
            print(f"正在抓取: {source_name}")
            feedparser.USER_AGENT = USER_AGENT

            @retry_on_failure(max_retries=2, delay=1)
            def fetch_feed():
                return feedparser.parse(feed_url)

            feed = fetch_feed()
            if not feed or not hasattr(feed, "entries") or not feed.entries:
                continue

            for entry in feed.entries[:6]:
                raw_title = entry.get("title", "无标题")
                raw_summary = (entry.get("summary", "") or "")

                # 对默认认为是英文的源尝试翻译为中文
                if source_name in ENGLISH_SOURCES:
                    title_zh = translate_text(raw_title)
                    summary_zh = translate_text(raw_summary)[:150] + "..." if raw_summary else ""
                else:
                    title_zh = raw_title
                    summary_zh = raw_summary[:150] + "..." if raw_summary else ""

                news_item = {
                    "source": source_name,
                    "title": raw_title,
                    "title_zh": title_zh,
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "summary": summary_zh,
                    "summary_raw": raw_summary,
                }
                if category in categorized_news:
                    categorized_news[category].append(news_item)

            success_count += 1
            time.sleep(1)

        except Exception:
            print(f"  ✗ 抓取失败: {source_name}")
            continue

    print(f"\n抓取完成，成功获取 {success_count} 个数据源。")
    return categorized_news


def analyze_hot_sectors(categorized_news: dict[str, list[dict]]) -> list[tuple[str, list[dict]]]:
    """分析新闻中提到的热门板块（基于标题+摘要的关键词共振）"""
    sector_mentions: dict[str, list[dict]] = {sector: [] for sector in SECTOR_KEYWORDS.keys()}

    all_news: list[dict] = []
    for items in categorized_news.values():
        all_news.extend(items)

    for news in all_news:
        text = (news.get("title", "") or "") + " " + (news.get("summary", "") or "")
        for sector, keywords in SECTOR_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    sector_mentions[sector].append(
                        {
                            "title": news.get("title", ""),
                            "source": news.get("source", ""),
                            "link": news.get("link", ""),
                        }
                    )
                    break

    hot_sectors = sorted(
        [(sector, items) for sector, items in sector_mentions.items() if items],
        key=lambda x: len(x[1]),
        reverse=True,
    )[:5]
    return hot_sectors


def get_hot_stocks(hot_sector_names: list[str]) -> list[dict]:
    """
    量化多因子选股算法 (结合趋势、动能、量价与热点)
    使用 yfinance 批量高速下载一个月的数据进行计算
    """
    print("\n正在使用量化多因子算法高速筛选 A股主板 (约 6000 只股票)...")
    stocks_data: list[dict] = []
    chunk_size = 500  # 批量下载大小

    for i in range(0, len(SAMPLE_STOCKS), chunk_size):
        chunk = SAMPLE_STOCKS[i : i + chunk_size]
        try:
            print(f"  处理进度: {i} - {i + len(chunk)} ...")
            data = yf.download(chunk, period="1mo", group_by="ticker", threads=True, progress=False)

            for symbol in chunk:
                if symbol not in data:
                    continue
                df = data[symbol]

                if (
                    not isinstance(df, pd.DataFrame)
                    or df.empty
                    or "Close" not in df.columns
                    or "Volume" not in df.columns
                ):
                    continue

                c = df["Close"].dropna()
                v = df["Volume"].dropna()

                if len(c) < 20:
                    continue

                current_price = c.iloc[-1]
                prev_price = c.iloc[-2]
                if prev_price <= 0:
                    continue
                change_pct = (current_price - prev_price) / prev_price * 100

                if change_pct <= 0:
                    continue

                sma20 = c.tail(20).mean()

                if len(v) < 6:
                    continue
                avg_vol_5 = v.tail(6).iloc[:5].mean()
                vol_ratio = v.iloc[-1] / avg_vol_5 if avg_vol_5 > 0 else 0

                delta = c.diff()
                gain = delta.where(delta > 0, 0).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                if loss.iloc[-1] == 0 or pd.isna(loss.iloc[-1]):
                    continue
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs.iloc[-1]))

                # === 强力打分系统 (满分 100分) ===
                score = 0

                # 1. 趋势均线得分 (满分25) - 站上20日均线得满分
                if current_price > sma20:
                    trend_score = 25
                else:
                    trend_score = max(0, 25 - ((sma20 - current_price) / sma20 * 500))
                score += trend_score

                # 2. 动能 RSI 得分 (满分25)
                if 50 <= rsi <= 70:
                    rsi_score = 25
                elif 40 <= rsi < 50:
                    rsi_score = 15
                elif rsi > 70:
                    rsi_score = 10
                else:
                    rsi_score = 0
                score += rsi_score

                # 3. 量价异动得分 (满分20)
                if vol_ratio >= 2.0:
                    vol_score = 20
                elif vol_ratio >= 1.5:
                    vol_score = 15
                elif vol_ratio >= 1.0:
                    vol_score = 5
                else:
                    vol_score = 0
                score += vol_score

                # 4. 热门板块共振得分 (满分30)
                stock_name = get_stock_name(symbol)
                sector_score = 0
                for sector_name in hot_sector_names:
                    for keyword in SECTOR_KEYWORDS.get(sector_name, []):
                        if keyword in stock_name:
                            sector_score = 30
                            break
                    if sector_score > 0:
                        break

                if sector_score == 0 and vol_ratio > 1.8 and trend_score == 25 and rsi_score == 25:
                    sector_score = 20

                score += sector_score

                if score >= 75:
                    stocks_data.append(
                        {
                            "code": symbol.split(".")[0],
                            "name": stock_name,
                            "price": float(current_price),
                            "change_pct": float(change_pct),
                            "vol_ratio": float(vol_ratio),
                            "rsi": float(rsi),
                            "score": int(score),
                            "details": f"趋势:{int(trend_score)} 动能:{int(rsi_score)} 量能:{int(vol_score)} 题材:{int(sector_score)}",
                        }
                    )

        except Exception:
            continue

    sorted_stocks = sorted(stocks_data, key=lambda x: x["score"], reverse=True)[:10]
    return sorted_stocks


def format_email_content(
    categorized_news: dict[str, list[dict]],
    hot_sectors: list[tuple[str, list[dict]]],
    hot_stocks: list[dict],
) -> str:
    """生成层次分明、设计美观的HTML邮件内容"""
    today = datetime.now().strftime("%Y年%m月%d日")

    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Microsoft YaHei', sans-serif; line-height: 1.6; color: #333; background: #f4f6f9; margin: 0; padding: 20px; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
            .header {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 25px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 24px; }}
            .content-pad {{ padding: 25px; }}
            .section-title {{ font-size: 20px; font-weight: bold; color: #1e3c72; margin: 30px 0 15px 0; padding-left: 10px; border-left: 5px solid #ff4757; }}

            .warning-box {{ background: #fff3cd; border: 1px solid #ffeeba; color: #856404; padding: 12px; border-radius: 6px; font-size: 13px; margin-bottom: 15px; }}
            .stock-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            .stock-table th {{ background: #f1f2f6; color: #2f3542; padding: 12px; text-align: left; font-size: 14px; border-bottom: 2px solid #dfe4ea; }}
            .stock-table td {{ padding: 12px; border-bottom: 1px solid #f1f2f6; font-size: 14px; }}
            .stock-table tr:hover {{ background: #fafafa; }}
            .price-up {{ color: #ff4757; font-weight: bold; }}
            .score-badge {{ background: #ff4757; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 13px; }}
            .detail-text {{ font-size: 11px; color: #747d8c; display: block; margin-top: 4px; }}

            .category-wrapper {{ margin-bottom: 25px; }}
            .cat-title {{ background: #f1f2f6; display: inline-block; padding: 5px 15px; border-radius: 20px; font-size: 14px; font-weight: bold; color: #2f3542; margin-bottom: 15px; border-left: 3px solid #3742fa; }}
            .news-card {{ background: #ffffff; border: 1px solid #f1f2f6; border-radius: 8px; padding: 15px; margin-bottom: 10px; transition: transform 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }}
            .news-source {{ font-size: 12px; color: #ffffff; background: #3742fa; padding: 3px 8px; border-radius: 4px; margin-right: 10px; }}
            .news-title {{ font-size: 16px; font-weight: bold; margin: 10px 0 5px 0; color: #2f3542; }}
            .news-title a {{ text-decoration: none; color: inherit; }}
            .news-title a:hover {{ color: #ff4757; }}
            .news-summary {{ font-size: 13px; color: #747d8c; line-height: 1.5; }}

            .footer {{ text-align: center; color: #a4b0be; font-size: 12px; padding: 20px; border-top: 1px solid #f1f2f6; background: #fafafa; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📈 USTCB 全球量化资讯日报</h1>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">{today} · AI大模型 | 全球宏观 | A股量化严选</p>
            </div>
            <div class="content-pad">
    """

    # 1. 算法严选 A 股
    html += '<div class="section-title">🎯 量化引擎严选 A股标的 (Top 10)</div>'
    if hot_stocks:
        html += """
        <div class="warning-box">
            <b>💡 算法说明：</b>采用 SMA均线(定趋势) + RSI强弱(寻多头) + 均量突破比率(抓异动资金) + 题材词频共振 进行满分100分的严苛筛选。仅作技术参考，不构成投资依据！
        </div>
        <table class="stock-table">
            <tr>
                <th>股票名称</th>
                <th>现价</th>
                <th>日涨幅</th>
                <th>量比(对5日)</th>
                <th>RSI(14)</th>
                <th>量化评分</th>
            </tr>
        """
        for stock in hot_stocks:
            html += f"""
            <tr>
                <td><b>{stock['name']}</b><br><span style="color:#a4b0be;font-size:12px;">{stock['code']}</span></td>
                <td class="price-up">¥{stock['price']:.2f}</td>
                <td class="price-up">+{stock['change_pct']:.2f}%</td>
                <td>{stock['vol_ratio']:.1f}x</td>
                <td>{stock['rsi']:.1f}</td>
                <td>
                    <span class="score-badge">{stock['score']} 分</span>
                    <span class="detail-text">{stock['details']}</span>
                </td>
            </tr>
            """
        html += "</table>"
    else:
        html += '<p style="color:#747d8c;">今日无符合严苛筛选标准的标的，建议防守观望。</p>'

    # 2. 全市场资讯 (按分类渲染)
    html += '<div class="section-title">📰 全球前沿与财经要闻</div>'

    display_order = ["AI大模型", "美股与全球", "A股与国内"]
    for cat in display_order:
        news_list = categorized_news.get(cat, [])
        if not news_list:
            continue

        html += '<div class="category-wrapper">'
        html += f'<div class="cat-title">{cat} 资讯</div>'

        for news in news_list:
            html += f"""
            <div class="news-card">
                <div><span class="news-source">{news['source']}</span></div>
                <div class="news-title"><a href="{news['link']}" target="_blank">{news['title']}</a></div>
                <div class="news-summary">{news['summary']}</div>
            </div>
            """
        html += "</div>"

    html += """
            </div>
            <div class="footer">
                USTCB 全球数据聚合系统 · 由 GitHub Actions 驱动<br>
                投资有风险，入市需谨慎
            </div>
        </div>
    </body>
    </html>
    """
    return html


def send_email(content: str, recipient_email: str, smtp_password: str) -> bool:
    sender_email = recipient_email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🌍 宏观视角·量化精选日报 - {datetime.now().strftime('%Y-%m-%d')}"
    msg["From"] = sender_email
    msg["To"] = recipient_email

    msg.attach(MIMEText(content, "html", "utf-8"))

    try:
        server = smtplib.SMTP("smtp.qq.com", 587)
        server.starttls()
        server.login(sender_email, smtp_password)
        server.send_message(msg)
        server.quit()
        print(f"✅ 完美！邮件已成功投递至: {recipient_email}")
        return True
    except Exception as e:
        print(f"❌ 邮件投递失败: {str(e)}")
        return False


def main() -> None:
    print("=" * 60)
    print("USTCB 全球资讯与量化引擎启动")
    print("=" * 60)

    recipient_email = os.getenv("QQ_EMAIL")
    smtp_password = os.getenv("QQ_SMTP_PASSWORD")

    if not recipient_email or not smtp_password:
        print("❌ 错误: 环境缺失 QQ_EMAIL 或 QQ_SMTP_PASSWORD")
        return

    print("\n📡 阶段1: 开始扫描全网 RSS 资讯...")
    categorized_news = fetch_rss_news()

    print("\n🔥 阶段2: 分析当日热点板块（用于题材共振打分）...")
    hot_sectors = analyze_hot_sectors(categorized_news)
    hot_sector_names = [sector for sector, _ in hot_sectors]
    if hot_sector_names:
        print(f"✓ 锁定热点: {', '.join(hot_sector_names)}")

    print("\n📈 阶段3: 激活量化多因子选股引擎...")
    hot_stocks = get_hot_stocks(hot_sector_names)

    print("\n📝 阶段4: 渲染日报 HTML 内容...")
    email_content = format_email_content(categorized_news, hot_sectors, hot_stocks)

    print("📧 阶段5: 投递邮件...")
    send_email(email_content, recipient_email, smtp_password)

    print("=" * 60)
    print("所有任务执行完毕！祝您投资顺利。")


if __name__ == "__main__":
    main()

