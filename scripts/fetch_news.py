#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股财经新闻RSS聚合与邮件推送
每日自动抓取主要财经网站的RSS新闻并发送到邮箱
"""

import os
import smtplib
import feedparser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import time

# RSS源列表 - 主要财经网站
RSS_FEEDS = {
    '新浪财经-股票': 'https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k=&num=20&page=1&r=0.5',
    '东方财富-要闻': 'http://feed43.com/eastmoney-news.xml',
    '证券时报': 'http://news.stcn.com/sd/rss.xml',
    '财联社快讯': 'https://rsshub.app/cls/telegraph',
    '第一财经': 'https://rsshub.app/yicai/brief',
    '金融界-股票': 'https://rsshub.app/jrj/stock',
    '东方财富-板块': 'https://rsshub.app/eastmoney/stock/bk',
    '同花顺-热点': 'https://rsshub.app/10jqka/news/stock',
    '雪球-热门': 'https://rsshub.app/xueqiu/hots',
}

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

def fetch_rss_news():
    """抓取所有RSS源的新闻"""
    all_news = []

    for source_name, feed_url in RSS_FEEDS.items():
        try:
            print(f"正在抓取: {source_name}")
            feed = feedparser.parse(feed_url)

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

            # 避免请求过快
            time.sleep(1)

        except Exception as e:
            print(f"抓取 {source_name} 失败: {str(e)}")
            continue

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

def format_email_content(news_list, hot_sectors):
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
            .news-item {{ border-left: 4px solid #667eea; padding: 15px;
                         margin: 15px 0; background: #f9f9f9; }}
            .source {{ color: #667eea; font-weight: bold; font-size: 14px; }}
            .title {{ font-size: 16px; font-weight: bold; margin: 8px 0; }}
            .summary {{ color: #666; font-size: 14px; margin: 8px 0; }}
            .link {{ color: #764ba2; text-decoration: none; }}
            .footer {{ text-align: center; color: #999; padding: 20px;
                      border-top: 1px solid #ddd; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📈 A股财经日报</h1>
            <p>{today}</p>
        </div>
        <div style="padding: 20px;">
    """

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
                板块热度基于新闻提及次数统计，仅供参考
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
    print(f"✅ 发现 {len(hot_sectors)} 个热门板块\n")

    # 3. 格式化邮件内容
    print("📝 正在格式化邮件内容...")
    email_content = format_email_content(news_list, hot_sectors)

    # 4. 发送邮件
    print("📧 正在发送邮件...")
    success = send_email(email_content, recipient_email, smtp_password)

    if success:
        print("\n🎉 任务完成！")
    else:
        print("\n⚠️ 任务完成但邮件发送失败")

    print("=" * 50)

if __name__ == '__main__':
    main()
