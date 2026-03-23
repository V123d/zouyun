# 🍽️ 走云智能排菜系统 (ZouYun Smart Menu Planning System)

> 基于多智能体协同 (Multi-Agent) + 大语言模型 (LLM) 的中学食堂智能排菜系统，已迈入生产可用阶段。

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-compose-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org)
[![React](https://img.shields.io/badge/React-19+-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![Qwen](https://img.shields.io/badge/LLM-通义千问_Qwen--max-7C3AED)](https://dashscope.aliyun.com)

---

## 📖 项目简介

走云智能排菜系统是一款面向团餐后厨的 **AI 辅助排菜工具**，旨在将传统的人工排菜流程（通常耗时数小时）缩短至 **分钟级**。系统通过 **"表单结构化约束 + 自然语言对话微调"** 的双轨输入模式，让用户既能通过表单精确配置餐标预算、菜品分类、烹饪工艺等硬性约束，也能通过自然语言灵活表达"下周降温多排驱寒菜"等临时意图。

系统最新版本已引入 **用户认证体系** 与 **持久化关系型数据库 (SQLite)**，具备更高的安全性和多用户数据隔离能力。

### 核心业务价值

| 传统人工排菜 | 走云智能排菜 |
|---|---|
| 营养师手动翻查食谱，耗时 2-4 小时 | AI 一键生成一周菜单，耗时 30 秒 |
| 凭经验估算成本，存在超标风险 | 系统自动核算食材成本，实时告警 |
| 难以兼顾多种约束（红线、过敏、营养） | 多智能体交叉校验，100% 满足硬约束 |
| 菜品重复率高，学生抱怨 | 智能去重算法，重复率 ≤ 20% |

---

## 🏗️ 系统架构

### 核心架构 (v2.2+)

系统采用 **独立智能体 + 编排器** 的业务架构，并以 **FastAPI + SQLAlchemy + JWT** 为核心提供服务支撑：

```
┌─────────────────────────────────────────────────────────────────┐
│                      前端 (React + TypeScript)                    │
│                                                                 │
│  ┌──────────────┐  ┌───────────────┐  ┌─────────────────────┐  │
│  │  安全层       │  │  日历看板     │  │  对话与配置         │  │
│  │ (AuthPage)   │  │ CalendarDash  │  │ AgentChat/Config    │  │
│  └──────┬───────┘  └───────┬───────┘  └──────────┬──────────┘  │
│         │                  │                     │              │
│  ┌──────┴──────────────────┼─────────────────────┘              │
│  │ Zustand 全局状态 (AuthStore / AppStore)                     │
│  └─────────────────────────┼────────────────────────────────────│
│                            ▼                                    │
│             API 服务层 (SSE 流式 / RESTful API / JWT Auth)       │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP / Server-Sent Events
┌────────────────────────────┼────────────────────────────────────┐
│                        后端 (FastAPI)                            │
│                                                                 │
│  ┌───────────────── 安全防护与路由分发 ──────────────────────┐  │
│  │   AuthRouter / MenuRouter / ChatRouter / AgentRouter    │  │
│  └─────────────────────────┬───────────────────────────────┘  │
│                            │                                  │
│  ┌──────────────────── 编排器 (Orchestrator) ──────────────────┐ │
│  │                                                            │ │
│  │  ┌─────────────┐   ┌───────────────┐   ┌───────────────┐  │ │
│  │  │  ① Intent   │ → │  ② Menu       │ → │ ③ Constraint  │  │ │
│  │  │   Parser    │   │   Generator   │   │   Checker     │  │ │
│  │  │  意图解析    │   │   菜单生成     │   │  约束校验      │  │ │
│  │  │  (LLM)     │   │   (LLM)       │   │  (规则引擎)    │  │ │
│  │  └─────────────┘   └───────────────┘   └───────┬───────┘  │ │
│  │                                                │           │ │
│  │                     ┌──────────────────────────┐│           │ │
│  │                     │ 不通过 → 自动重排 (≤2次)  ││           │ │
│  │                     └──────────────────────────┘│           │ │
│  │                                                ▼           │ │
│  │                                       ┌───────────────┐    │ │
│  │                                       │ ④ Data        │    │ │
│  │                                       │  Enrichment   │    │ │
│  │                                       │  数据补全      │    │ │
│  │                                       └───────────────┘    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────────── 持久化存储层 (SQLite) ──────────────────┐  │
│  │  ORM: SQLAlchemy (Async) | 数据模型: UserModel, MenuModel  │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 智能体注册表

| # | 智能体 ID | 名称 | 类型 | 职责 |
|:---:|---|---|:---:|---|
| ① | `intent-parser` | 意图解析智能体 | LLM | 将自然语言指令解析为结构化排菜需求 |
| ② | `menu-generator` | 菜单生成智能体 | LLM | 从菜品库中选菜，组装一周菜单 |
| ③ | `constraint-checker` | 约束校验智能体 | 规则 | 红线扫描、预算检查、重复率计算（确定性校验） |
| ④ | `data-enrichment` | 数据补全智能体 | 规则 | 将紧凑菜单补全为包含完整属性的菜品数据 |

> **可扩展性设计**：新增智能体只需继承 `BaseAgent` 基类并定义 `agent_id`/`agent_name`/`agent_description`，即可自动注册到注册表和 API 路由中，前端面板也会自动展示新智能体。

### 技术栈

| 层级 | 技术 | 版本 | 用途 |
|---|---|---|---|
| **前端框架** | React + TypeScript | 19.x / 5.7 | 组件化 UI 开发，类型安全 |
| **样式方案** | Tailwind CSS | 4.x | 原子化 CSS，快速构建精美 UI |
| **状态管理** | Zustand | 5.x | 全局状态管理 (含业务与认证) |
| **后端框架** | FastAPI | 0.115+ | 高性能异步 API 框架 |
| **数据库** | SQLite + aiosqlite | 3.x | 异步关系型数据库接入 |
| **ORM层** | SQLAlchemy | 2.0+ | 对象关系映射模型 |
| **认证控制** | PyJWT + Passlib | 2.8+ | JWT 令牌生成与密码哈希 |
| **LLM 接口** | OpenAI SDK (兼容) | 1.50+ | 调用通义千问 Qwen-max |
| **数据校验** | Pydantic | 2.0+ | 请求/响应模型强类型校验 |

---

## 📂 项目结构

```text
走云智能排菜系统/
├── start.bat                              # 🚀 开发环境一键启动脚本
├── docker-compose.yml                     # 🐳 生产级容器化服务自动编排网关
├── docs/                                  # 🆕 项目产品文档与示意图归档
├── frontend/                              # 前端 React 应用
│   ├── Dockerfile                        # 前端多阶段构建配置 (Node -> Nginx)
│   ├── nginx.conf                        # 生产级 Nginx 配置 (SPA、反代、SSE)
│   ├── src/
│   │   ├── pages/
│   │   │   └── AuthPage.tsx              # 🆕 用户登录/注册鉴权页
│   │   ├── components/
│   │   │   ├── layout/                   # 包含概览区与智能体面板
│   │   │   ├── chat/                     # 智能对话窗口
│   │   │   ├── config-drawer/            # 深度规则配置抽屉
│   │   │   └── calendar/                 # 周菜单日历看板
│   │   ├── stores/
│   │   │   ├── auth-store.ts             # 🆕 Zustand 鉴权状态管理
│   │   │   └── app-store.ts              # Zustand 业务表单状态
│   │   ├── services/
│   │   │   └── api.ts                    # API 调用层 (携带 Token)
│   │   ├── App.tsx                       # 主应用入口 (安全拦截过滤)
│   │   └── index.css                     # 设计系统
│   └── vite.config.ts                    # Vite 构建配置 (含跨域代理)
│
├── backend/                               # 后端 FastAPI 应用
│   ├── Dockerfile                        # 生产级 Gunicorn 多进程基座配置
│   ├── app/
│   │   ├── main.py                       # 入口、路由挂载、自带 RotatingFile 日志系统
│   │   ├── config.py                     # 配置管理 (API Key / JWT 解析)
│   │   ├── database.py                   # 🆕 SQLAlchemy 数据库引擎配置
│   │   ├── security.py                   # 🆕 JWT / Token / 密码加解密逻辑
│   │   ├── models/                       # 🆕 DB 数据模型存放
│   │   ├── schemas/                      # Pydantic 校验模型
│   │   ├── routers/
│   │   │   ├── auth_router.py            # 🆕 用户认证 (注册/登录/获取)
│   │   │   ├── chat_router.py            # 对话 SSE 路由
│   │   │   ├── agent_router.py           # 智能体独立调用路由
│   │   │   ├── menu_router.py            # 🆕 菜单存储与拉取
│   │   │   └── dish_router.py            # 菜品库数据路由
│   │   ├── services/
│   │   │   ├── base_agent.py             # 智能体基类 + 自动注册
│   │   │   ├── intent_parser.py          # ① 意图解析智能体
│   │   │   ├── menu_generator.py         # ② 菜单生成智能体
│   │   │   └── orchestrator.py           # 多智能体编排器等
│   │   └── data/
│   │       └── dish_library.json         # 菜品库 Mock 数据 (可逐步迁移至 DB)
│   ├── init_db.py                        # 🆕 初始化 SQLite 数据库建表脚本
│   ├── requirements.txt                  # Python 依赖清单
│   └── .env.example                      # 环境变量模板
│
└── README.md
```

---

## 🧠 核心功能实现详解

### 1. 安全认证与持久化存储 (生产级)

系统增加了完整的认证机制与数据库打通，且原生支持容灾开发/生产双重配置：
- **安全鉴权**：采用 OAuth2 Password Bearer 搭配 `PyJWT`，密码使用 `Bcrypt` 强哈希存储。所有涉及数据拉取的接口皆受 `JWT Token` 保护（动态读取 `JWT_SECRET_KEY` 配置）。
- **兼容读写的持久化**：使用核心 `SQLAlchemy 2.0+` 构建底层对象模型。开发状态默认使用轻量级 `sqlite+aiosqlite` 快速拉起；部署时将通过 Compose 挂载完整的 **PostgreSQL 集群 (`asyncpg` 驱动)**，彻底杜绝 SQLite 多用户并行写入时的死锁。
- **持久化稳固日志**：脱离了简单的控制台黑窗打印，将全局日志统一收束并拦截于 `logs/app.log` 中，支持多进程下平滑的自动超量截断和归档保护。

### 2. 多智能体协同 (Multi-Agent Orchestration)

系统由 4 个独立智能体组成，通过编排器 (`orchestrator.py`) 串联协同：

```
用户指令 → ① 意图解析 → ② 菜单生成 → ③ 约束校验 → ④ 数据补全 → 持久化/前端展示
  │      (支持日期/餐次提取)               ↑        │            │
  │                                        └── 不通过 ┘ (自动重排)  │
  └────────────────── 携带当前菜单上下文发起多轮局部微调 ──────────────┘
```

与常规 LLM 智能体不同，约束校验智能体采用 **纯 Python 确定性逻辑**（扫描红线食材、检查预算超标、计算重复率等），保证排出的菜单合规且安全。

### 3. SSE 流式通信 (Server-Sent Events)

AI 生成长链条任务往往耗时长达数秒甚至几十秒。系统采用 SSE 流式推断实时通信，分别在各个智能体环节推送 `thinking` 和 `content` 等状态，前端实现类打字机体验和状态气泡跟踪。

### 4. 前端双轨输入模式

- **结构化表单**：支持配置 7 种食堂场景，自定义动态控制餐次（人数/入口率/餐标）与菜品分类栅格，加上健康状态、禁忌与全局红线组合。
- **自然语言对话**：通过智能对话窗口下发全局或**局部多轮微调**指令（如：“把周四的午餐全换成素菜”）。这依赖于 **Intent Parser** 对日期与餐次的精细化解耦输出。

---

## 🚀 快速开始

### 环境依赖
- **开发依赖**: Node.js ≥ 18.x, Python ≥ 3.10
- **生产部署依赖**: Docker Desktop / Engine
- **通义千问 API Key** ([申请地址](https://dashscope.console.aliyun.com/))

### 方式一：开发环境启动（适合日常修改与调试）

1. 克隆项目兵配置基础密钥：
```bash
git clone https://github.com/V123d/dish-organization-system.git
cd dish-organization-system
copy backend\.env.example backend\.env
```
2. **编辑 `backend/.env`，必须填入 `LLM_API_KEY`**。
3. 双击根目录下的 `start.bat` 一键启动（默认调用 SQLite 并自动初始化建表）。

---

### 方式二：生产级容器化无感极速部署（推荐线上首选）

项目已完成全量微服务（Web/API/DB）上云改造。对于无编程基础的环境或是线上服务器：

**您只需要在项目根目录运行一行代码：**
```bash
docker-compose up -d --build
```

**发生了什么？**
1. Docker 会拉取最新的 `postgres:15-alpine` 建立完全并行的多用户数据库中心。
2. 后端采用工业级 `Gunicorn + UvicornWorker` 接管多并发长链接生成。
3. 前端自动化编译通过 `Nginx` 微服务器构建完毕，彻底摆脱 `npm` 进程泄漏与报错依赖，内置解决了跨域重定向与反代理 SSE 穿透。

### 各服务端入口

| 服务 | 开发版地址 | 生产/容器版地址 |
|---|---|---|
| 👩‍💻 前端应用 | http://localhost:5173 | **http://localhost:5173** (Nginx代理暴露) |
| 🔌 后台 API / 健康 | http://localhost:8000/docs | http://localhost:8000/docs |
| 🗄️ 数据库连接池 | `./backend/data/app.db` (SQLite) | `postgesql://zouyun_user:***@db:5432` |
| 📝 生产业务日志审计 | — | `./backend/logs/app.log` |

---

## 🔌 常用 API 接口

### 认证接口 (Auth)

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/api/auth/register` | 注册新食堂账号 |
| `POST` | `/api/auth/login` | 账号密码登录 (返回 JWT Access Token) |
| `GET` | `/api/auth/me` | 获取当前用户信息 (需要 Token) |

### 排菜核心与排餐计划接口

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/api/chat/send` | 智能排菜对话 (SSE 接口，串联多智能体) |
| `POST` | `/api/menu/save` | 保存并归档一份已生成的智能排餐计划 |
| `GET` | `/api/menu/history` | 拉取当前用户的历史排餐计划列表 |

### 智能体底层级接口

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/api/agents/intent-parser` | 独立调用意图解析 |
| `POST` | `/api/agents/menu-generator` | 独立调用菜单生成 |
| `GET` | `/api/agents` | 获取所有已注册智能体信息 |

---

## 🗺️ 后续开发路线

### 现阶核心能力 (✓ 已完成)
- [x] 基于 Multi-Agent 架构自动化组菜
- [x] 多轮交互式对话与局部重排微调
- [x] SSE 全链路日志流
- [x] 确定性规则校验拦截告警引擎
- [x] 用户认证与安全控制隔离
- [x] **[基建]** PostgreSQL/SQLite 双切式关系型持久化存储
- [x] **[基建]** 包含 Dockerfile 及 docker-compose 的全量生产级容器化打包
- [x] **[基建]** Gunicorn 多进程异步高并发控制与 Rotating 文件日志监控

### Phase 3 — 智能体增强矩阵
- [ ] 营养分析智能体 (Nutrition Analyzer)— 精确计算 DRIs 达标率
- [ ] 成本控制智能体 (Cost Controller)— 对接实时生鲜价格网络
- [ ] 反馈学习智能体 (Feedback Learner)— 智能推荐与菜品学习闭环

### Phase 4 — 产业化部署
- [ ] 系统对接外部生鲜供应商 API (ERP 等)
- [ ] 一键导出采购清单与菜品成本卡
- [ ] Docker 化集群部署体系
- [ ] 适配手持移动终端与多平台发布

---

## 📄 许可证

MIT License

---

## 🙏 致谢

- [通义千问 Qwen](https://dashscope.aliyun.com/) — 提供大语言模型 API
- [FastAPI](https://fastapi.tiangolo.com/) — 高性能 Python Web 框架
- [SQLAlchemy](https://www.sqlalchemy.org/) — 高效的对象关系建立
- [React](https://react.dev/) — 视图构建框架
- [Tailwind CSS](https://tailwindcss.com/) — 原子化 CSS
- [Zustand](https://github.com/pmndrs/zustand) — 轻量级状态管理
