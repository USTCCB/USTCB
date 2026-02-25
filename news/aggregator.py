"""
news/aggregator.py
抓取 RSS 新闻 + 财联社电报 + 雪球热帖
v2.0：并发抓取，大幅提升速度
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict

import feedparser
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0 Safari/537.36"
    )
}


@dataclass
class NewsItem:
    title: str
    link: str
    summary: str = ""
    source: str = ""
    published: str = ""
    category: str = ""


def _fetch_rss(url: str, category: str, source_name: str, max_items: int = 8) -> List[NewsItem]:
    """抓取单个 RSS 源"""
    items: List[NewsItem] = []
    try:
        feed = feedparser.parse(url, request_headers=HEADERS)
        for entry in feed.entries[:max_items]:
            summary = entry.get("summary", "")
            # 清理 HTML 标签
            if "<" in summary:
                summary = BeautifulSoup(summary, "html.parser").get_text(separator=" ")
            summary = summary[:200].strip()

            published = ""
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    published = datetime(*entry.published_parsed[:6]).strftime("%m-%d %H:%M")
                except Exception:
                    pass

            items.append(NewsItem(
                title=entry.get("title", "（无标题）").strip(),
                link=entry.get("link", url),
                summary=summary,
                source=source_name,
                published=published,
                category=category,
            ))
    except Exception as e:
        logger.warning(f"RSS抓取失败 [{source_name}]: {e}")
    return items


def _fetch_cls_telegraph() -> List[NewsItem]:
    """财联社电报最新快讯（非RSS）"""
    items: List[NewsItem] = []
    try:
        url = "https://www.cls.cn/telegraph"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup.select(".telegraph-content-box")[:10]:
            text = tag.get_text(separator=" ", strip=True)[:200]
            if text:
                items.append(NewsItem(
                    title=text[:60],
                    link=url,
                    summary=text,
                    source="财联社电报",
                    category="A股财经",
                ))
    except Exception as e:
        logger.warning(f"财联社电报抓取失败: {e}")
    return items


def _fetch_xueqiu_hot() -> List[NewsItem]:
    """雪球热帖（话题热度最高的讨论）"""
    items: List[NewsItem] = []
    try:
        url = "https://xueqiu.com/v4/statuses/public_timeline_by_category.json?since_id=-1&max_id=-1&count=10&category=-1"
        resp = requests.get(url, headers={**HEADERS, "Referer": "https://xueqiu.com/"}, timeout=10)
        data = resp.json()
        for s in data.get("list", []):
            text = BeautifulSoup(s.get("text", ""), "html.parser").get_text()[:200]
            items.append(NewsItem(
                title=text[:60].strip(),
                link=f"https://xueqiu.com{s.get('target', '')}",
                summary=text,
                source="雪球热帖",
                category="A股财经",
            ))
    except Exception as e:
        logger.warning(f"雪球热帖抓取失败: {e}")
    return items


def fetch_all_news(rss_sources: Dict[str, List[str]]) -> Dict[str, List[NewsItem]]:
    """
    并发抓取所有新闻，返回按分类整理的字典  (v2.0 并发版)
    rss_sources: {分类名: [url, ...]}
    """
    result: Dict[str, List[NewsItem]] = {cat: [] for cat in rss_sources}

    # 构建所有抓取任务
    tasks = []
    for category, urls in rss_sources.items():
        for url in urls:
            source_name = url.split("/")[2]
            tasks.append((category, url, source_name))

    # 并发抓取（最多12个线程）
    logger.info(f"并发抓取 {len(tasks)} 个RSS源...")
    with ThreadPoolExecutor(max_workers=12) as executor:
        future_map = {
            executor.submit(_fetch_rss, url, category, source_name, 7): (category, url)
            for category, url, source_name in tasks
        }
        for future in as_completed(future_map):
            category, url = future_map[future]
            try:
                items = future.result(timeout=15)
                result[category].extend(items)
            except Exception as e:
                logger.debug(f"RSS任务失败 [{url[:40]}]: {e}")

    # 去重 & 截断
    for category in result:
        seen = set()
        deduped = []
        for item in result[category]:
            key = item.title[:30]
            if key not in seen:
                seen.add(key)
                deduped.append(item)
        result[category] = deduped[:15]
        logger.info(f"  → {category}: 获取 {len(result[category])} 条新闻")

    # 并发补充财联社电报 & 雪球热帖
    with ThreadPoolExecutor(max_workers=2) as ex:
        f_cls = ex.submit(_fetch_cls_telegraph)
        f_xq  = ex.submit(_fetch_xueqiu_hot)
        try:
            cls_news = f_cls.result(timeout=15)
        except Exception:
            cls_news = []
        try:
            xq_news = f_xq.result(timeout=15)
        except Exception:
            xq_news = []

    result["A股财经"] = (cls_news + result.get("A股财经", []) + xq_news)[:20]

    return result
