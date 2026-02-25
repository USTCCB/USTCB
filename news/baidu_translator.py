"""
百度翻译API模块
"""
import hashlib
import random
import requests
import logging
import os
from typing import List
from news.aggregator import NewsItem

logger = logging.getLogger(__name__)

BAIDU_APPID = os.getenv("BAIDU_TRANSLATE_APPID", "")
BAIDU_SECRET = os.getenv("BAIDU_TRANSLATE_SECRET", "")


def translate_news(items: List[NewsItem]) -> List[NewsItem]:
    """翻译新闻标题和摘要"""
    if not BAIDU_APPID or not BAIDU_SECRET:
        logger.warning("未配置百度翻译API，保持英文原文")
        return items
    
    translated = []
    for item in items:
        try:
            # 翻译标题
            title_cn = translate_text(item.title)
            # 翻译摘要（如果有且不太长）
            summary_cn = ""
            if item.summary and len(item.summary) < 500:
                summary_cn = translate_text(item.summary)
            
            translated.append(NewsItem(
                title=title_cn if title_cn else item.title,
                link=item.link,
                summary=summary_cn if summary_cn else item.summary,
                source=item.source,
                published=item.published,
                category=item.category,
            ))
        except Exception as e:
            logger.debug(f"翻译失败，保持原文: {e}")
            translated.append(item)
    
    return translated


def translate_text(text: str) -> str:
    """
    使用百度翻译API翻译文本
    文档: https://fanyi-api.baidu.com/doc/21
    """
    if not text or not BAIDU_APPID or not BAIDU_SECRET:
        return text
    
    # 如果文本已经是中文，直接返回
    if any('\u4e00' <= char <= '\u9fff' for char in text[:20]):
        return text
    
    try:
        # 生成签名
        salt = str(random.randint(32768, 65536))
        sign_str = BAIDU_APPID + text + salt + BAIDU_SECRET
        sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
        
        # 调用API
        url = "https://fanyi-api.baidu.com/api/trans/vip/translate"
        params = {
            'q': text,
            'from': 'en',
            'to': 'zh',
            'appid': BAIDU_APPID,
            'salt': salt,
            'sign': sign
        }
        
        response = requests.get(url, params=params, timeout=5)
        result = response.json()
        
        if 'trans_result' in result and len(result['trans_result']) > 0:
            translated = result['trans_result'][0]['dst']
            logger.debug(f"翻译成功: {text[:30]}... -> {translated[:30]}...")
            return translated
        else:
            logger.warning(f"翻译失败: {result.get('error_msg', 'Unknown error')}")
            return text
            
    except Exception as e:
        logger.debug(f"翻译API调用失败: {e}")
        return text
