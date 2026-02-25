# 📈 USTCB — 全球财经 & AI 资讯日报（GitHub Actions 版）

每天全自动：抓取 A股/美股/港股大事、AI大模型动态、热门板块、热门股票，
用多因子量化算法选出最优 A 股候选，精美 HTML 邮件每日准时发到你的邮箱。

---

## 🚀 五步完成部署

### 第一步：Fork 本仓库

点击页面右上角 **Fork** 按钮，把仓库复制到你的账号下。

---

### 第二步：配置邮箱 Secrets

进入你 Fork 后的仓库 → **Settings → Secrets and variables → Actions → New repository secret**

添加以下三个 Secret（名称必须完全一致）：

| Secret 名称 | 值 |
|---|---|
| `USTCB_EMAIL_SENDER` | 你的 QQ 邮箱地址，如 `123456@qq.com` |
| `USTCB_EMAIL_PASSWORD` | QQ 邮箱 **SMTP 授权码**（不是登录密码）|
| `USTCB_EMAIL_TO` | 收件人邮箱，多个用逗号分隔 |

> **QQ 邮箱授权码获取方式**：
> 登录 QQ 邮箱网页版 → 设置 → 账户 → POP3/IMAP/SMTP 服务 → 开启 → 短信验证 → 生成授权码

---

### 第三步：启用 Actions

进入仓库 **Actions** 标签页 → 点击绿色按钮 **"I understand my workflows, go ahead and enable them"**

---

### 第四步：手动测试运行

Actions → 左侧找到 **📈 USTCB 每日财经日报** → 右侧 **Run workflow** → **Run workflow**

等待约 3~5 分钟，查看你的邮箱是否收到日报。

---

### 第五步：等待自动运行

每天自动运行两次（北京时间）：
- **08:00** — 开盘前 · 全球隔夜行情 + AI资讯
- **15:30** — 收盘后 · A股复盘 + 量化选股结果

---

## 📧 日报内容

| 板块 | 数据来源 |
|------|--------|
| 📊 全球指数 | 上证/深成/创业板/沪深300/科创50/恒生/道指/纳指/标普500 |
| 🇨🇳 A股财经要闻 | 华尔街见闻、格隆汇、36氪、虎嗅 |
| 🇺🇸 美股要闻 | CNBC、WSJ、MarketWatch、SeekingAlpha |
| 🇭🇰 港股要闻 | HKEx、阿斯达克 |
| 🤖 AI大模型 | OpenAI、Anthropic、Google AI、HuggingFace、DeepMind、TechCrunch AI |
| 🔥 热门板块 | 行业 ETF 涨跌幅实时榜（新能源/半导体/AI/医药…） |
| 💥 热门股票 | 监控池中今日涨幅 Top-N |
| 🎯 量化选股 | **10 因子多维度评分**选出 A 股买入候选 |

---

## 🧠 多因子选股算法

```
技术面（60%）
├── MACD 金叉         12%
├── 5日动量           12%
├── 20日动量          10%
├── RSI健康区间       10%
├── KDJ 金叉           8%
└── 布林带位置         8%

资金面（18%）
├── 量比               10%
└── 换手率代理          8%

估值面（12%）
└── PE 评分            12%

外部资金（10%）
└── 北向资金代理        8%（总权重归一化）
```

**选股流程**：
1. 监控 A 股精选 100 支（沪深300核心+行业龙头）
2. 拉取 90 日日线 K 线数据（Yahoo Finance）
3. 计算 10 个因子，加权综合评分
4. 过滤涨停/跌停边缘股，输出 Top-10 + 买入信号 + 风险提示

---

## 📁 项目结构

```
.
├── .github/
│   └── workflows/
│       └── daily_report.yml   ← GitHub Actions 核心配置
├── main.py                    ← 主入口
├── config.py                  ← 股票池、权重、RSS源配置
├── requirements.txt
├── core/
│   └── runner.py              ← 流程编排
├── news/
│   ├── aggregator.py          ← 新闻抓取（RSS + 去重）
│   └── market_data.py         ← 行情数据（yfinance）
├── selectors/
│   └── multi_factor.py        ← 10因子量化选股
└── templates/
    └── email_builder.py       ← 精美 HTML 邮件
```

---

## ⚙️ 自定义

**修改发送时间**（`daily_report.yml`）：
```yaml
- cron: '0 0 * * 1-5'    # UTC 00:00 = 北京 08:00
- cron: '30 7 * * 1-5'   # UTC 07:30 = 北京 15:30
```

**调整选股因子权重**（`config.py`）：
```python
FACTOR_WEIGHTS = {
    "macd_signal": 0.20,   # 更偏技术面
    "pe_score":    0.20,   # 更偏价值投资
    ...
}
```

**修改股票监控池**：编辑 `config.py` 中的 `STOCK_POOL_CN`

---

## ⚠️ 免责声明

本项目为技术学习项目，选股结果**仅供参考，不构成投资建议**。
股票市场存在风险，投资需谨慎，盈亏自负。
