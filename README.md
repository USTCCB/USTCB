# 📈 USTCB - A股财经新闻日报

每天自动抓取主要财经网站的RSS新闻，并通过邮件发送到QQ邮箱。

## 📰 新闻源

- 新浪财经 - 股票要闻
- 东方财富 - 财经要闻
- 证券时报 - 市场动态
- 财联社 - 快讯
- 第一财经 - 财经简讯
- 金融界 - 股票资讯

## 🚀 快速开始

### 1. Fork或克隆本仓库

```bash
git clone https://github.com/你的用户名/USTCB.git
cd USTCB
```

### 2. 设置GitHub Secrets

在GitHub仓库中设置以下Secrets（Settings → Secrets and variables → Actions → New repository secret）：

| Secret名称 | 值 | 说明 |
|-----------|---|------|
| `QQ_EMAIL` | `2403148578@qq.com` | 你的QQ邮箱地址 |
| `QQ_SMTP_PASSWORD` | `你的授权码` | QQ邮箱SMTP授权码（不是QQ密码） |

### 3. 启用GitHub Actions

- 进入仓库的 **Actions** 标签页
- 点击 **I understand my workflows, go ahead and enable them**
- 工作流将在每天北京时间早上8点自动运行

### 4. 手动测试

在 **Actions** 页面，选择 **Daily Financial News** 工作流，点击 **Run workflow** 手动触发测试。

## 📧 如何获取QQ邮箱SMTP授权码

1. 登录 [QQ邮箱网页版](https://mail.qq.com)
2. 点击 **设置** → **账户**
3. 找到 **POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务**
4. 开启 **IMAP/SMTP服务**
5. 点击 **生成授权码**，按提示操作
6. 保存生成的授权码（16位字母，如：abcdEFGHijklMNOP）

## ⚙️ 自定义配置

### 修改发送时间

编辑 `.github/workflows/daily-news.yml` 中的 cron 表达式：

```yaml
schedule:
  - cron: '0 0 * * *'  # UTC时间，北京时间需+8小时
```

示例：
- `0 0 * * *` - 每天北京时间8:00
- `0 23 * * *` - 每天北京时间7:00
- `0 1 * * *` - 每天北京时间9:00

### 添加更多RSS源

编辑 `scripts/fetch_news.py` 中的 `RSS_FEEDS` 字典：

```python
RSS_FEEDS = {
    '你的源名称': 'RSS链接',
    # 添加更多...
}
```

## 📝 本地测试

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export QQ_EMAIL="2403148578@qq.com"
export QQ_SMTP_PASSWORD="你的授权码"

# 运行脚本
python scripts/fetch_news.py
```

## ⚠️ 免责声明

本项目仅用于技术学习和信息聚合，所提供的新闻内容来自公开RSS源，**不构成任何投资建议**。投资有风险，决策需谨慎。

## 📄 许可证

MIT License
