# 走云智能排菜系统 (ZouYun Smart Menu Planning System)

> 基于多智能体协同 (Multi-Agent) + 大语言模型 (LLM) 的中学食堂智能排菜系统，已迈入生产可用阶段。

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19+-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![Qwen](https://img.shields.io/badge/LLM-通义千问_Qwen--max-7C3AED)](https://dashscope.aliyun.com)

---

## 项目简介

走云智能排菜系统是一款面向团餐后厨的 **AI 辅助排菜工具**，将传统人工排菜流程（通常耗时数小时）缩短至 **分钟级**。系统通过"表单结构化约束 + 自然语言对话微调"的双轨输入模式，让用户既能通过表单精确配置餐标预算、菜品分类等硬性约束，也能通过自然语言灵活表达"下周降温多排驱寒菜"等临时意图。

### 核心业务价值

| 对比项 | 传统人工排菜 | 走云智能排菜 |
|--------|------------|------------|
| 排菜耗时 | 2-4 小时 | **30 秒** |
| 成本控制 | 凭经验估算，存在超标风险 | 系统自动核算，实时告警 |
| 约束满足 | 难以兼顾多种约束 | 多智能体交叉校验 |
| 菜品重复率 | 高，学生抱怨多 | 智能去重算法，重复率 ≤ 20% |

---

## 系统架构

### 核心技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 前端框架 | React 19 + TypeScript | 组件化 UI 开发 |
| 样式方案 | Tailwind CSS 4.x | 原子化 CSS |
| 状态管理 | Zustand 5.x | 全局状态管理 |
| 后端框架 | FastAPI 0.115+ | 高性能异步 API |
| 数据库 | SQLite (开发) / PostgreSQL (生产) | 持久化存储 |
| ORM层 | SQLAlchemy 2.0+ (异步) | 对象关系映射 |
| 认证控制 | PyJWT + Passlib | JWT 令牌认证 |
| LLM 接口 | OpenAI SDK (兼容通义千问) | 调用 Qwen-max |

### 智能体架构 (Multi-Agent Orchestration)

系统由 4 个独立智能体组成，通过编排器串联协同：

```
用户指令 → ① 意图解析 → ② 菜单生成 → ③ 约束校验 → ④ 数据补全 → 前端展示
  │      (支持日期/餐次提取)               ↑        │
  │                                        └── 不通过 ┘ (自动重排)
  └──────────────── 携带当前菜单上下文发起多轮局部微调 ──┘
```

| # | 智能体 ID | 名称 | 类型 | 职责 |
|:---:|---|---|:---:|---|
| ① | `intent-parser` | 意图解析智能体 | LLM | 将自然语言指令解析为结构化排菜需求 |
| ② | `menu-generator` | 菜单生成智能体 | LLM | 从菜品库中选菜，组装一周菜单 |
| ③ | `constraint-checker` | 约束校验智能体 | 规则引擎 | 红线扫描、预算检查、重复率计算 |
| ④ | `data-enrichment` | 数据补全智能体 | 规则引擎 | 将紧凑菜单补全为含完整属性的菜品数据 |

> **可扩展性**：新增智能体只需继承 `BaseAgent` 基类并定义 `agent_id`/`agent_name`，即可自动注册到注册表和 API 路由中。

### 系统架构图

```
┌──────────────────────────────────────────────────────────────────┐
│                        前端 (React + TypeScript)                   │
│  ┌─────────────┐  ┌─────────────────┐  ┌──────────────────────┐  │
│  │  登录/注册   │  │   日历看板       │  │  对话窗口 / 规则配置   │  │
│  └─────────────┘  └─────────────────┘  └──────────────────────┘  │
│                           │                                        │
│                     Zustand 全局状态                                 │
│                           ▼                                        │
│               API 服务层 (SSE 流式 / REST / JWT)                   │
└────────────────────────────┬─────────────────────────────────────┘
                             │ HTTP / SSE
┌────────────────────────────▼─────────────────────────────────────┐
│                        后端 (FastAPI + SQLAlchemy)                   │
│                                                                     │
│  编排器 (Orchestrator)                                              │
│  ├── ① Intent Parser  → ② Menu Generator → ③ Constraint Checker │
│  │                                        ↓                         │
│  │                               不通过 → 自动重排 (最多1次)            │
│  │                                        ↓                         │
│  │                              ④ Data Enrichment                   │
│  │                                                                │
│  持久化层: SQLite (开发) / PostgreSQL (生产)                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 项目结构

```
走云智能排菜系统/
├── start.bat               # 🚀 开发环境一键启动脚本
├── docker-compose.yml     # 🐳 生产级容器化编排
├── frontend/              # 前端 React 应用
│   ├── src/
│   │   ├── pages/AuthPage.tsx          # 用户登录/注册
│   │   ├── components/
│   │   │   ├── layout/                 # 布局组件
│   │   │   │   ├── ContextHeader.tsx  # 全局概览区
│   │   │   │   └── AgentPanel.tsx     # 智能体状态面板
│   │   │   ├── chat/                  # 对话组件
│   │   │   │   ├── AgentChat.tsx      # 智能排菜对话窗口
│   │   │   │   └── HistoryDrawer.tsx  # 历史记录抽屉
│   │   │   ├── calendar/              # 日历看板
│   │   │   │   ├── CalendarDashboard.tsx
│   │   │   │   └── MenuModals.tsx
│   │   │   ├── config-drawer/         # 规则配置抽屉
│   │   │   │   └── ConfigDrawer.tsx
│   │   │   ├── database/              # 数据库管理
│   │   │   │   ├── DatabaseManager.tsx
│   │   │   │   ├── DishLibraryManager.tsx  # 菜品库管理
│   │   │   │   └── StandardQuotaManager.tsx
│   │   │   ├── nutrition-quota/      # 营养配额面板
│   │   │   └── quota-editor/         # 配额编辑器
│   │   ├── stores/
│   │   │   ├── auth-store.ts         # 认证状态
│   │   │   └── app-store.ts          # 业务状态
│   │   ├── services/api.ts           # API 调用层
│   │   └── types/index.ts            # TypeScript 类型定义
│   ├── Dockerfile
│   └── nginx.conf
│
└── backend/               # 后端 FastAPI 应用
    ├── app/
    │   ├── main.py                    # 入口、路由挂载
    │   ├── config.py                  # 配置管理 (API Key / JWT)
    │   ├── database.py               # SQLAlchemy 数据库配置
    │   ├── security.py                # JWT / Token / 密码加解密
    │   ├── models/                   # ORM 数据模型
    │   │   ├── user.py
    │   │   ├── dish.py
    │   │   ├── history.py
    │   │   ├── chat_session.py
    │   │   └── standard_quota.py
    │   ├── schemas/                  # Pydantic 校验模型
    │   ├── routers/                  # API 路由
    │   │   ├── auth_router.py        # 认证 (注册/登录)
    │   │   ├── chat_router.py        # 对话 SSE 路由
    │   │   ├── agent_router.py       # 智能体独立调用
    │   │   ├── menu_router.py        # 菜单存储与拉取
    │   │   ├── dish_router.py        # 菜品库 CRUD
    │   │   └── standard_quota_router.py
    │   └── services/                 # 核心业务逻辑
    │       ├── base_agent.py          # 智能体基类 + 自动注册
    │       ├── intent_parser.py       # ① 意图解析
    │       ├── menu_generator.py      # ② 菜单生成
    │       ├── constraint_checker.py  # ③ 约束校验
    │       ├── data_enrichment.py     # ④ 数据补全
    │       ├── orchestrator.py        # 多智能体编排器
    │       ├── dish_quantity_calculator.py  # 份数计算
    │       └── utils.py               # 共享工具函数
    └── requirements.txt
```

---

## 核心功能

### 1. 多智能体协同编排

- **意图解析**：从自然语言中提取日期、餐次、偏好、预算等结构化信息
- **菜单生成**：按天并行生成，支持预筛选候选菜品（token 消耗降低 80%）
- **约束校验**：确定性规则引擎，支持红线扫描、预算检查、跨天重复检查、主配料去重
- **数据补全**：将 LLM 返回的紧凑格式（仅 id/name）补全为含完整属性的菜品数据
- **自动重试**：约束不通过时自动重排（单日最多 1 次）

### 2. SSE 流式通信

AI 生成长链条任务耗时数秒甚至几十秒。系统采用 SSE 流式推送，前端实时显示：
- `thinking` — 各智能体处理步骤
- `menu_partial_update` — 流式增量菜单渲染
- `menu_update` — 逐天菜单填充
- `constraint_alert` — 具体不合格项告警
- `daily_quota_update` — 每日营养配额达标数据
- `menu_result` — 最终菜单结果

### 3. 深度规则配置

- 7 类灶别营养标准（配料分类配额 / 营养素配额双模式）
- 动态餐次配置（人数、入口率、餐标）
- 菜品分类栅格自定义
- 健康状态、饮食禁忌与全局红线

### 4. 份数自动计算

根据「食堂菜品结构」和「个人菜品结构」自动计算每道菜的排菜份数：
```
某分类每道份数 = ceil(就餐人数 × 个人该分类份数 / 食堂该分类菜品数量)
```

---

## 快速开始

### 环境依赖

- Node.js ≥ 18.x、Python ≥ 3.10
- 通义千问 API Key（[申请地址](https://dashscope.console.aliyun.com/)）

### 开发环境

```bash
# 克隆项目
git clone https://gitea.gouzill.com/paddle_project/zouyun.git
cd zouyun

# 配置 API Key
copy backend\.env.example backend\.env
# 编辑 backend/.env，填入 LLM_API_KEY

# 一键启动
./start.bat
```

- 前端：http://localhost:5173
- 后端 API：http://localhost:8000/docs

### 生产环境 (Docker)

```bash
docker-compose up -d --build
```

---

## 主要 API

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 注册账号 |
| POST | `/api/auth/login` | 登录（返回 JWT） |
| GET | `/api/auth/me` | 获取当前用户信息 |

### 排菜

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat/send` | 智能排菜对话（SSE 流式） |
| POST | `/api/menu/history` | 保存排餐计划 |
| GET | `/api/menu/history` | 拉取历史列表 |

### 数据管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/dishes/library` | 获取菜品库 |
| POST | `/api/dishes/` | 创建菜品 |
| GET | `/api/standard-quotas/` | 获取营养配额配置 |

---

## 开发路线

### 已完成

- [x] Multi-Agent 自动化组菜
- [x] 多轮对话与局部重排微调
- [x] SSE 全链路流式通信
- [x] 确定性规则校验拦截
- [x] JWT 用户认证与数据隔离
- [x] SQLite / PostgreSQL 双模式持久化
- [x] Docker 容器化部署
- [x] 份数自动计算

### 后续规划

- [ ] 营养分析智能体 — 精确计算 DRIs 达标率
- [ ] 成本控制智能体 — 对接实时生鲜价格
- [ ] 反馈学习智能体 — 菜品推荐闭环
- [ ] 一键导出采购清单
- [ ] 适配移动端

---

## 许可证

MIT License
