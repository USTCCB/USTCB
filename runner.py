"""
runner.py
日报生成主流程编排器 - 添加翻译功能
"""

import logging
import os
from datetime import datetime

from config import (
    EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENTS,
    SMTP_HOST, SMTP_PORT,
    RSS_SOURCES, FACTOR_WEIGHTS,
    TOP_STOCKS_COUNT, SECTOR_TOP_N, MARKET_TOP_N,
    STOCK_POOL, CACHE_DIR,
)
from news.aggregator import fetch_all_news
from news.market_hot import (
    fetch_hot_sectors, fetch_hot_stocks,
    fetch_north_fund_flow, fetch_market_overview,
)
from news.baidu_translator import translate_news
from stock_selectors.multi_factor import run_selector
from templates.email_builder import build_html_email
from utils.mailer import send_html_email

logger = logging.getLogger(__name__)


class DailyRunner:

    def run(self):
        today = datetime.now().strftime("%Y-%m-%d")
        os.makedirs(CACHE_DIR, exist_ok=True)

        # ── 1. 拉取数据 ───────────────────────────────
        logger.info("步骤 1/6：抓取新闻资讯...")
        news = fetch_all_news(RSS_SOURCES)

        logger.info("步骤 2/6：翻译英文新闻...")
        # 翻译美股和AI新闻
        if "美股要闻" in news:
            news["美股要闻"] = translate_news(news["美股要闻"])
        if "AI大模型" in news:
            news["AI大模型"] = translate_news(news["AI大模型"])

        logger.info("步骤 3/6：获取市场行情...")
        indices = fetch_market_overview()
        north_flow = fetch_north_fund_flow()
        hot_sectors = fetch_hot_sectors(top_n=SECTOR_TOP_N)
        hot_stocks = fetch_hot_stocks(stock_pool=STOCK_POOL, top_n=MARKET_TOP_N)

        logger.info("步骤 4/6：运行多因子量化选股...")
        top_picks = run_selector(
            weights=FACTOR_WEIGHTS,
            top_n=TOP_STOCKS_COUNT,
            stock_pool=STOCK_POOL if STOCK_POOL else None,
        )

        # ── 2. 生成 HTML ──────────────────────────────
        logger.info("步骤 5/6：生成 HTML 日报...")
        html = build_html_email(
            date_str=today,
            indices=indices,
            news_by_category=news,
            hot_sectors=hot_sectors,
            hot_stocks=hot_stocks,
            top_picks=top_picks,
            north_flow=north_flow,
        )

        # 保存 HTML 到本地
        html_path = os.path.join(CACHE_DIR, f"report_{today}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info(f"HTML 报告已保存: {html_path}")

        # ── 3. 发送邮件 ───────────────────────────────
        logger.info("步骤 6/6：发送邮件...")
        now = datetime.now()
        time_label = "早报" if now.hour < 12 else "晚报"
        subject = f"📈 财经{time_label} {today} | A股/美股/港股要闻 + AI动态 + 量化选股"
        
        ok = send_html_email(
            sender=EMAIL_SENDER,
            password=EMAIL_PASSWORD,
            recipients=EMAIL_RECIPIENTS,
            subject=subject,
            html_body=html,
            smtp_host=SMTP_HOST,
            smtp_port=SMTP_PORT,
        )
        if not ok:
            logger.warning("邮件发送失败，但 HTML 报告已保存到本地")
        return html_path
