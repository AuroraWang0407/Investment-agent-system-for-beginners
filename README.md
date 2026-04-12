# 📈 智能股票投资助手 | AI Stock Investment Assistant

一个基于 LangChain 和 DeepSeek LLM 的课程项目，为初学者提供股票投资建议和风险分析。

A course project powered by LangChain and DeepSeek LLM, providing stock investment advice and risk analysis for beginners.

---

## 🎯 项目功能 | Features

- **实时股票查询** | Real-time Stock Quotes：获取最新价格、涨跌幅、交易量
- **公司信息分析** | Company Profile：行业、市值、商业概述
- **投资头寸计算** | Position Sizing：根据预算和风险偏好计算购买数量
- **风险收益分析** | Risk-Reward Ratio：评估交易的风险-收益比
- **最新消息摘要** | News Sentiment：获取相关股票新闻
- **参数管理** | Parameter Management：跟踪投资金额、股票代码、止损百分比
- **Web UI** | Streamlit Interface：友好的可视化界面
- **REST API** | FastAPI Backend：后端 API 支持
- **智能评估** | Auto Evaluation：在 LangSmith 上自动评估模型性能

---

## 📋 项目结构 | Project Structure

```
agent_4070/
├── scripts/                    # 主要源代码
│   ├── agent_runner.py        # 主智能体（Agent）运行逻辑
│   ├── agent_tools.py         # LLM 工具定义
│   ├── app.py                 # Streamlit Web UI
│   ├── api.py                 # FastAPI 后端
│   ├── eval_agent.py          # LangSmith 评估脚本
│   ├── custom_evaluator.py    # 自定义评估器
│   ├── data.py                # 测试数据
│   └── requirements.txt        # Python 依赖
├── backup/                     # 旧版本备份代码
├── .env.example               # 环境变量示例（含说明）
├── .env                       # 实际环境变量（请勿提交！）
├── .gitignore                 # Git 忽略文件
└── README.md                  # 本文件
```

---

## 🚀 快速开始 | Quick Start

### 前置条件 | Prerequisites

- **Python 3.8+**
- **Anaconda** (推荐) 或其他 Python 环境管理工具
- **有效的 DeepSeek API 密钥** ([获取](https://api.deepseek.com))

### 安装步骤 | Installation

#### 1️⃣ 克隆项目 | Clone Repository
```bash
git clone <your-repo-url>
cd agent_4070
```

#### 2️⃣ 创建虚拟环境 | Create Virtual Environment
```bash
# 使用 Conda
conda create -n stock_agent python=3.10
conda activate stock_agent

# 或使用 venv
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
```

#### 3️⃣ 安装依赖 | Install Dependencies
```bash
cd scripts
pip install -r requirements.txt
```

#### 4️⃣ 配置环境变量 | Configure Environment Variables
```bash
# 在项目根目录创建 .env 文件（从模板复制）
cp .env.example .env

# 编辑 .env，填入你的 API 密钥
# 必填项:
#   - DEEPSEEK_API_KEY: 你的 DeepSeek API 密钥
# 可选项:
#   - LANGCHAIN_API_KEY: LangSmith 费用追踪（仅用于评估）
```

---

## 💻 使用方式 | Usage

### 方法 1️⃣：命令行交互 | CLI Mode
```bash
cd scripts
python agent_runner.py

# 输入投资问题
# 示例:
#   "我想投入 1000 块钱买 AAPL，最多亏 5%"
#   "TSLA 和 NVDA 哪个适合初学者？"
#   "分析一下 MSFT"
```

### 方法 2️⃣：Streamlit Web UI | Web Interface
```bash
cd scripts
streamlit run app.py

# 浏览器自动打开 http://localhost:8501
```

**功能特色：**
- 🌐 全球市场概览（S&P 500、NASDAQ、黄金、VIX）
- 📊 实时市场状态（开盘/闭盘倒计时）
- 💬 多轮对话支持
- 🌍 多语言支持（中文/English）

### 方法 3️⃣：FastAPI 后端 | REST API
```bash
cd scripts
uvicorn api:app --reload

# API 文档访问: http://localhost:8000/docs
```

**API 端点:**
```bash
# POST /api/invest
curl -X POST "http://localhost:8000/api/invest" \
  -H "Content-Type: application/json" \
  -d '{"user_input":"我想投1000块买AAPL"}'
```

### 方法 4️⃣：LangSmith 评估 | Evaluation
```bash
cd scripts

# 确保 .env 中配置了 LANGCHAIN_API_KEY
python eval_agent.py

# 前往 https://smith.langchain.com 查看评估结果
```

---

## 🛠️ 核心工具说明 | Tools Explanation

Agent 可以自动调用以下工具：

| 工具 | 功能 | 返回数据 |
|-----|------|---------|
| `get_current_quote` | 获取实时股票报价 | 价格、涨跌幅、交易量 |
| `get_company_profile` | 获取公司基本信息 | 行业、市值、周期比率 |
| `get_recent_news` | 获取最新财经新闻 | Yahoo Finance 新闻摘要 |
| `calculate_position_size` | 计算购买数量 | 股数、止损价、最大亏损额 |
| `analyze_risk_reward` | 分析风险-收益比 | 单股风险、潜在收益、比率 |
| `get_investment_params` | 读取当前投资参数 | 股票代码、投资金额、止损% |
| `update_investment_params` | 更新投资参数 | 确认信息 |

---

## ⚙️ 环境变量设置 | Configuration

### 必填项 | Required
```env
DEEPSEEK_API_KEY=sk-xxxx...              # DeepSeek API 密钥
DEEPSEEK_MODEL=deepseek-chat             # 模型名称
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
```

### 可选项 | Optional
```env
# LangSmith 评估（仅用于 eval_agent.py）
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_pt_xxxx...
LANGCHAIN_PROJECT=stock-agent-evaluation
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

# 应用设置
APP_TEMPERATURE=0.1                      # Agent 创意度（0-1）
EVAL_TEMPERATURE=0.0                     # 评估器精确度（0）
```

---

## 📝 示例对话 | Example Queries

```
用户: "我有 5000 块钱，想买 NFLX，最多可以亏 8%"
Agent: [调用工具] → 获取 NFLX 价格、公司信息、最新新闻
        计算头寸大小 → 风险分析
        → "根据当前价格，你可以购买 X 股，止损价在 $Y，最大损失 $Z..."

用户: "改成 TSLA 试试"
Agent: [缓存前面的对话] → 更新股票代码
        → 重新计算、分析...

用户: "TSLA 和 NVDA 哪个更适合初学者？"
Agent: [比较两只股票] → 波动率、新闻情绪、风险概况
        → "对于初学者，TSLA 波动较大...NVDA 相对稳定..."
```

---

## 🧪 测试与评估 | Testing

该项目包含 10 个预定义的测试用例（见 `data.py`）：

```python
TEST_CASES = [
    "Which is better for beginners, TSLA or NVDA?",
    "I want to buy $1000 of AAPL with 5% stop",
    "change it to $2000",
    ...
]
```

运行评估：
```bash
python eval_agent.py
# 自动上传到 LangSmith
# 查看评分：safe_compliance, answer_relevance, hallucination, tool_calling_ability
```

---

## ⚠️ 免责声明 | Disclaimer

**本项目仅为教学演示用途，不构成真实财务或投资建议。**

所有建议基于历史数据和市场情绪分析，未考虑个人财务状况。请在做出任何投资决定前，咨询专业财务顾问。

---

## 📚 技术栈 | Tech Stack

| 组件 | 库/框架 |
|------|--------|
| LLM Framework | LangChain |
| LLM Model | DeepSeek Chat |
| Web UI | Streamlit |
| Backend API | FastAPI + Uvicorn |
| Data Source | yfinance, Yahoo Finance |
| Evaluation | LangSmith |
| Environment | python-dotenv |

---

## 🐛 常见问题 | FAQ

### Q1: 运行时出现 "API key not found" 错误
**A:** 检查 `.env` 文件是否存在且包含 `DEEPSEEK_API_KEY`
```bash
# 验证:
cat .env | grep DEEPSEEK_API_KEY
```

### Q2: yfinance 从 Yahoo Finance 获取数据很慢
**A:** 这是正常的。可以添加代理或使用本地缓存：
```python
# 在 agent_tools.py 中启用缓存
@st.cache_data(ttl=300)  # 缓存 5 分钟
def get_current_quote(...):
    ...
```

### Q3: Streamlit 无法连接到 FastAPI
**A:** 确保 FastAPI 服务正在运行：
```bash
cd scripts
uvicorn api:app --reload
```

### Q4: 如何在生产环境中安全使用？
**A:** 
- ❌ 勿将 `.env` 提交到 Git（已在 `.gitignore` 中）
- ✅ 使用系统环境变量或密钥管理服务（如 AWS Secrets Manager）
- ✅ 定期轮换 API 密钥

---

## 📧 联系方式 | Contact

有问题或建议？请提交 Issue 或 Pull Request。

---

## 📄 许可证 | License

本项目仅供学习使用。课程完成后可根据需要修改许可证。

---

**最后更新 | Last Updated:** 2026-04-12  
**项目状态 | Status:** 🟢 Production Ready (for coursework)
