"""
新闻翻译模块 - 将英文新闻标题翻译成中文
"""
import logging
import os
import requests
from typing import List
from news.aggregator import NewsItem

logger = logging.getLogger(__name__)

TRANSLATE_API_URL = os.getenv("TRANSLATE_API_URL", "")


def translate_news(items: List[NewsItem]) -> List[NewsItem]:
    """
    翻译新闻标题和摘要
    如果没有配置翻译API，则保持原文
    """
    if not TRANSLATE_API_URL:
        logger.warning("未配置翻译API，保持英文原文")
        return items
    
    translated = []
    for item in items:
        try:
            # 翻译标题
            title_cn = _translate_text(item.title)
            # 翻译摘要（如果有）
            summary_cn = _translate_text(item.summary) if item.summary else ""
            
            translated.append(NewsItem(
                title=title_cn or item.title,
                link=item.link,
                summary=summary_cn or item.summary,
                source=item.source,
                published=item.published,
                category=item.category,
            ))
        except Exception as e:
            logger.debug(f"翻译失败，保持原文: {e}")
            translated.append(item)
    
    return translated


def _translate_text(text: str) -> str:
    """
    调用翻译API翻译文本
    支持多种翻译服务
    """
    if not text or not TRANSLATE_API_URL:
        return text
    
    try:
        # 简单的翻译API调用（可以替换为其他翻译服务）
        response = requests.post(
            TRANSLATE_API_URL,
            json={"text": text, "target": "zh"},
            timeout=5
        )
        if response.status_code == 200:
            result = response.json()
            return result.get("translated_text", text)
    except Exception as e:
        logger.debug(f"翻译API调用失败: {e}")
    
    return text
