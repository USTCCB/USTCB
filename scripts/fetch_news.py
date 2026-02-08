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

def format_email_content(news_list):
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

    # 2. 格式化邮件内容
    print("📝 正在格式化邮件内容...")
    email_content = format_email_content(news_list)

    # 3. 发送邮件
    print("📧 正在发送邮件...")
    success = send_email(email_content, recipient_email, smtp_password)

    if success:
        print("\n🎉 任务完成！")
    else:
        print("\n⚠️ 任务完成但邮件发送失败")

    print("=" * 50)

if __name__ == '__main__':
    main()
