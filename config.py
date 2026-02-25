"""
config.py  —  USTCB 全局配置
所有敏感信息都从环境变量读取，配合 GitHub Secrets 使用
"""
import os

# ══ 邮件（填入 GitHub Secrets，字段名完全对应）══════════════════
EMAIL_SENDER     = os.getenv("USTCB_EMAIL_SENDER") or os.getenv("QQ_EMAIL", "your_qq@qq.com")
EMAIL_PASSWORD   = os.getenv("USTCB_EMAIL_PASSWORD") or os.getenv("QQ_SMTP_PASSWORD", "your_smtp_auth_code")
EMAIL_RECIPIENTS = (os.getenv("USTCB_EMAIL_TO") or os.getenv("QQ_EMAIL", "your_qq@qq.com")).split(",")
SMTP_HOST        = "smtp.qq.com"
SMTP_PORT        = 465

# ══ 运行模式 ════════════════════════════════════════════════════
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"  # true=只生成HTML不发邮件

# ══ 选股参数 ════════════════════════════════════════════════════
TOP_STOCKS_COUNT = 10    # 推荐 A股数量
SECTOR_TOP_N     = 6     # 热门板块数量
MARKET_TOP_N     = 8     # 热门股票数量

# ══ 多因子权重（合计 = 1.0） ════════════════════════════════════
FACTOR_WEIGHTS = {
    "momentum_5d":    0.12,
    "momentum_20d":   0.10,
    "volume_ratio":   0.10,
    "macd_signal":    0.12,
    "rsi_score":      0.10,
    "kdj_signal":     0.08,
    "boll_position":  0.08,
    "turnover_rate":  0.08,
    "pe_score":       0.12,
    "north_flow":     0.10,
}

# ══ RSS / 数据源（全部可被 GitHub Actions 访问的国际源）════════
RSS_SOURCES = {
    "A股财经": [
        "https://www.cls.cn/rss",                                    # 财联社（有国际访问）
        "https://www.jrj.com.cn/rss/index.shtml",                   # 金融界
        "https://www.investing.com/rss/news_301.rss",               # Investing China
        "https://cn.reuters.com/rssFeed/CNTopNews",                  # 路透中国
    ],
    "美股要闻": [
        "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US",
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
        "https://www.investing.com/rss/news_25.rss",
    ],
    "港股要闻": [
        "https://www.investing.com/rss/news_72.rss",
        "https://cn.reuters.com/rssFeed/HKTopNews",
    ],
    "AI大模型": [
        "https://openai.com/news/rss.xml",
        "https://www.anthropic.com/rss.xml",
        "https://blogs.microsoft.com/ai/feed/",
        "https://blog.google/technology/ai/rss/",
        "https://huggingface.co/blog/feed.xml",
        "https://www.deepmind.com/blog/rss.xml",
        "https://feeds.feedburner.com/venturebeat/SZYF",
        "https://techcrunch.com/category/artificial-intelligence/feed/",
    ],
}

# ══ 定时（scheduler.py 本地运行用，GitHub Actions 忽略此项）═══
SCHEDULE_HOUR   = 7
SCHEDULE_MINUTE = 30

# ══ 缓存目录 ════════════════════════════════════════════════════
CACHE_DIR = ".cache"
