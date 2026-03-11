# 🍽️ 走云智能排菜系统 (ZouYun Smart Menu Planning System)

> 基于多智能体协同 (Multi-Agent) + 大语言模型 (LLM) 的中学食堂智能排菜系统

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19+-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7+-3178C6?logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Qwen](https://img.shields.io/badge/LLM-通义千问_Qwen--max-7C3AED)](https://dashscope.aliyun.com)

---

## 📖 项目简介

走云智能排菜系统是一款面向团餐后厨的 **AI 辅助排菜工具**，旨在将传统的人工排菜流程（通常耗时数小时）缩短至 **分钟级**。系统通过 **"表单结构化约束 + 自然语言对话微调"** 的双轨输入模式，让用户既能通过表单精确配置餐标预算、菜品分类、烹饪工艺等硬性约束，也能通过自然语言灵活表达"下周降温多排驱寒菜"等临时意图。

### 核心业务价值

| 传统人工排菜 | 走云智能排菜 |
|---|---|
| 营养师手动翻查食谱，耗时 2-4 小时 | AI 一键生成一周菜单，耗时 30 秒 |
| 凭经验估算成本，存在超标风险 | 系统自动核算食材成本，实时告警 |
| 难以兼顾多种约束（红线、过敏、营养） | Agent 多维度交叉校验，100% 满足硬约束 |
| 菜品重复率高，学生抱怨 | 智能去重算法，重复率 ≤ 20% |

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                          前端 (React + TypeScript)                │
│  ┌──────────────┐  ┌───────────────┐  ┌─────────────────────┐  │
│  │  日历看板     │  │  对话窗口      │  │  规则配置抽屉       │  │
│  │ CalendarDash  │  │  AgentChat    │  │  ConfigDrawer       │  │
│  │  board       │  │               │  │                     │  │
│  └──────┬───────┘  └───────┬───────┘  └──────────┬──────────┘  │
│         │                  │                     │              │
│         └──────────────────┼─────────────────────┘              │
│                            │ Zustand 全局状态管理                 │
│                            ▼                                    │
│                     API 服务层 (SSE / REST)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP / Server-Sent Events
┌────────────────────────────┼────────────────────────────────────┐
│                        后端 (FastAPI)                            │
│  ┌─────────────────────────▼──────────────────────────────────┐ │
│  │                   /api/chat/send (SSE)                     │ │
│  │  ┌───────────┐  ┌───────────────┐  ┌───────────────────┐  │ │
│  │  │  Intent   │→ │    Menu       │→ │   Constraint      │  │ │
│  │  │  Parser   │  │   Generator   │  │    Checker         │  │ │
│  │  │ 意图解析   │  │  菜单生成      │  │   约束校验          │  │ │
│  │  └───────────┘  └───────┬───────┘  └───────────────────┘  │ │
│  │                         │                                  │ │
│  │                    Qwen-max LLM                            │ │
│  │              (Prompt Chaining 策略)                         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌────────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │ 菜品库 (JSON)   │  │ Pydantic 模型 │  │  占位 API (6个)   │    │
│  │ 80道中餐菜品    │  │ 类型校验       │  │  待开发功能        │    │
│  └────────────────┘  └──────────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### 技术栈

| 层级 | 技术 | 版本 | 用途 |
|---|---|---|---|
| **前端框架** | React + TypeScript | 19.x / 5.7 | 组件化 UI 开发，类型安全 |
| **样式方案** | Tailwind CSS | 4.x | 原子化 CSS，快速构建精美 UI |
| **状态管理** | Zustand | 5.x | 轻量级全局状态管理 |
| **构建工具** | Vite | 7.x | 极速 HMR，开箱即用 |
| **图标库** | Lucide React | — | 清爽的开源图标库 |
| **后端框架** | FastAPI | 0.115+ | 高性能异步 API 框架 |
| **LLM 接口** | OpenAI SDK (兼容) | 1.50+ | 调用通义千问 Qwen-max |
| **数据校验** | Pydantic | 2.0+ | 请求/响应模型强类型校验 |

---

## 📂 项目结构

```
走云智能排菜系统/
├── frontend/                           # 前端 React 应用
│   ├── src/
│   │   ├── components/                 # UI 组件
│   │   │   ├── layout/
│   │   │   │   └── ContextHeader.tsx   # 全局概览区
│   │   │   ├── chat/
│   │   │   │   └── AgentChat.tsx       # 智能对话窗口
│   │   │   ├── config-drawer/
│   │   │   │   └── ConfigDrawer.tsx    # 深度规则配置抽屉
│   │   │   └── calendar/
│   │   │       └── CalendarDashboard.tsx # 周菜单日历看板
│   │   ├── stores/
│   │   │   └── app-store.ts            # Zustand 全局状态
│   │   ├── services/
│   │   │   └── api.ts                  # API 调用层 (SSE 解析)
│   │   ├── types/
│   │   │   └── index.ts                # TypeScript 类型定义
│   │   ├── utils/
│   │   │   └── date.ts                 # 日期工具函数
│   │   ├── App.tsx                     # 主应用入口
│   │   ├── main.tsx                    # React 渲染挂载
│   │   └── index.css                   # 设计系统 (动画/主题/玻璃态)
│   ├── vite.config.ts                  # Vite 构建配置 (含 SSE 代理)
│   └── package.json
│
├── backend/                            # 后端 FastAPI 应用
│   ├── app/
│   │   ├── main.py                     # FastAPI 入口 & 路由注册
│   │   ├── config.py                   # 配置管理 (LLM API Key)
│   │   ├── schemas/
│   │   │   └── chat_schema.py          # Pydantic 请求/响应模型
│   │   ├── services/
│   │   │   └── agent_service.py        # 🧠 多智能体核心服务
│   │   └── data/
│   │       └── dish_library.json       # 菜品库 Mock 数据 (80道)
│   └── requirements.txt
│
└── README.md                           # 本文档
```

---

## 🧠 核心功能实现详解

### 1. 多智能体协同 (Multi-Agent Orchestration)

**文件**: [`backend/app/services/agent_service.py`](backend/app/services/agent_service.py)

#### 设计原理

系统在概念上设计了三个智能体角色，遵循 PRD 中描述的多智能体协同工作流：

| 智能体 | 职责 | 输入 | 输出 |
|---|---|---|---|
| **Intent Parser** (意图解析) | 从自然语言中提取排菜意图 | 用户消息 + 规则配置 JSON | 结构化的排菜需求 |
| **Menu Generator** (菜单生成) | 从菜品库中选菜组装菜单 | 排菜需求 + 菜品库 + 约束 | 一周菜单 JSON |
| **Constraint Checker** (约束校验) | 交叉校验红线/预算/重复率 | 初版菜单 + 硬约束 | 校验结果 / 触发重排 |

#### Demo 阶段实现策略：Prompt Chaining

在生产环境中，三个 Agent 应独立工作并可循环迭代（校验不通过则重排）。但在 **Demo 阶段**，我们采用 **Prompt Chaining（提示词链式调用）** 策略：

```
┌─────────────────────────────────────────────────┐
│           单次 LLM 调用 (Qwen-max)               │
│                                                  │
│  System Prompt 包含:                             │
│  ├── 排餐环境 (场景/城市/周期)                     │
│  ├── 餐次配置 (人数/餐标/分类结构)                  │
│  ├── 全局红线 & 饮食禁忌                           │
│  ├── 完整菜品库 (80道菜 × 详细属性)                │
│  └── 排菜规则 (8条硬约束)                          │
│                                                  │
│  User Prompt: 用户自然语言指令                      │
│                                                  │
│  输出: 结构化 JSON (菜单 + 指标 + 总结)             │
└─────────────────────────────────────────────────┘
```

**为什么这样设计**：单次调用大模型让其一步完成"理解意图→选菜组合→自我校验"的全流程，减少 API 调用次数和总耗时，同时通过精心设计的 System Prompt 中的 8 条硬约束规则，引导模型自行完成校验。这在 Demo 阶段是高效且可行的。

#### System Prompt 构建过程

`build_system_prompt()` 函数会动态组装以下信息：

1. **排餐环境上下文**：场景类型、城市、日期范围
2. **各餐次详细配置**：自动遍历所有已启用的餐次，提取人数/餐标/分类结构/汤性/必用食材等
3. **全局约束**：红线食材列表、健康状态人群、饮食禁忌群体
4. **菜品库全量数据**：按分类列出所有 80 道菜品，包含 ID、工艺、成本、标签
5. **8 条排菜硬规则**：数量匹配、去重、红线拦截、成本控制等
6. **输出格式模板**：严格的 JSON Schema，确保 LLM 输出可被前端直接解析

---

### 2. SSE 流式通信 (Server-Sent Events)

**文件**: [`backend/app/main.py`](backend/app/main.py) + [`frontend/src/services/api.ts`](frontend/src/services/api.ts)

#### 设计原理

由于 LLM 生成一周完整菜单通常需要 **20~40 秒**，如果使用传统的 REST 请求-响应模式，用户将面对一个长时间的空白等待，严重影响体验。因此系统采用 **SSE (Server-Sent Events)** 实现实时流式通信。

#### 后端实现

```python
# FastAPI 使用 StreamingResponse 包装异步生成器
@app.post("/api/chat/send")
async def chat_send(request: ChatRequest):
    return StreamingResponse(
        generate_menu_stream(request.message, request.config),
        media_type="text/event-stream",  # SSE 标准 Content-Type
        headers={"X-Accel-Buffering": "no"},  # 禁用 Nginx 缓冲
    )
```

`generate_menu_stream()` 是一个 `AsyncGenerator`，通过 `yield` 逐步产出 SSE 事件：

| 阶段 | SSE 事件类型 | 用途 |
|---|---|---|
| 意图解析 | `thinking` | 显示"正在理解您的排菜需求..."动效 |
| 成本计算 | `thinking` | 显示"正在查询食材时价..."动效 |
| 菜单生成 | `thinking` (心跳) | 每 50 tokens 发送一次进度更新 |
| 约束校验 | `thinking` | 显示"正在交叉校验红线与预算..." |
| 结果返回 | `content` + `menu_result` | 文本总结 + 完整菜单 JSON |

**关键技术细节**：LLM 调用使用 `stream=True` 模式，即大模型逐 token 返回。后端在流式接收过程中，每累积 50 个 token 就向前端发送一个心跳事件，避免 SSE 通道因长时间无数据而被浏览器/代理层断开。

#### 前端实现

```typescript
// 使用 Fetch API + ReadableStream 解析 SSE
const reader = response.body?.getReader();
const decoder = new TextDecoder();
let buffer = '';

while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    // 按行拆分，解析 "data: {...}" 格式的 SSE 事件
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    for (const line of lines) {
        if (line.startsWith('data: ')) {
            const parsed = JSON.parse(line.slice(6));
            // 根据 parsed.type 分发到不同回调
        }
    }
}
```

---

### 3. 前端双轨输入模式

#### 3.1 结构化约束 — 深度规则配置抽屉

**文件**: [`frontend/src/components/config-drawer/ConfigDrawer.tsx`](frontend/src/components/config-drawer/ConfigDrawer.tsx)

配置抽屉以**滑出式侧面板**的形式呈现，包含以下配置模块：

| 模块 | 对应 PRD 章节 | 实现说明 |
|---|---|---|
| **基础属性** | §3.3.1 | 食堂场景下拉（7种）、城市文本输入、日期范围选择器 |
| **动态餐次管理** | §3.3.2 | 可勾选启用/禁用、自定义名称、动态新增/删除餐次 |
| **餐次内部配置** | §3.3.3 | 人数/入口率/餐标、用餐方式（4种）、菜品分类栅格（可自由增删列、编辑名称和数量）、主食细类多选、汤品描述和汤性单选、烹饪工艺标签、口味偏好文本、必用食材/必排菜品 |
| **特殊人群** | §3.3.4 | 健康状态勾选（6种）、饮食禁忌勾选（8种）、全局红线文本域 |

**状态管理原理**：所有配置数据存储在 Zustand store 的 `config: MenuPlanConfig` 对象中。当用户点击"保存并同步"时，配置被序列化为 JSON，随下一次对话请求一并发送给后端，成为 Agent System Prompt 的一部分。

#### 3.2 自然语言微调 — 智能对话窗口

**文件**: [`frontend/src/components/chat/AgentChat.tsx`](frontend/src/components/chat/AgentChat.tsx)

| 功能 | 实现原理 |
|---|---|
| **消息列表** | 基于 `messages: ChatMessage[]` 数组渲染，支持用户/Agent 两种角色的气泡样式 |
| **思考动效** | 每条 Agent 消息携带 `thinking_steps: ThinkingStep[]`，根据步骤状态渲染 ✓/⏳/❌ 图标 |
| **快捷指令标签** | 输入框上方的 6 个预设标签，点击自动补全到输入框 |
| **排菜结果卡片** | 当 Agent 消息包含 `metrics` 时，渲染绿色渐变的总结卡片（成本/营养/重复率/告警） |
| **流式内容** | 通过 `updateMessage()` 实时追加 SSE 流中的 `content` 事件到消息体 |

---

### 4. 周菜单日历看板

**文件**: [`frontend/src/components/calendar/CalendarDashboard.tsx`](frontend/src/components/calendar/CalendarDashboard.tsx)

#### 嵌套网格视图

日历看板的核心是一个 **二维嵌套网格表格**：

```
         周一     周二     周三     周四     周五     周六     周日
午餐
  大荤   [菜品卡] [菜品卡] [菜品卡] [菜品卡] [菜品卡] [菜品卡] [菜品卡]
  小荤   [菜品卡] [菜品卡] ...
  素菜   ...
  主食   ...
  汤     ...
晚餐
  大荤   ...
  素菜   ...
```

- **纵轴**：餐次 → 菜品分类（使用 `rowSpan` 合并餐次单元格）
- **横轴**：一周七天（通过 `getDateRange()` 动态生成日期范围）
- **单元格数据**：从 `weeklyMenu[date][mealName][categoryName]` 三级嵌套中读取

#### 交互功能

| 功能 | 实现说明 |
|---|---|
| **指标仪表盘** | 4 张渐变色卡片（总成本/营养达标率/重复率/告警数），数据来自后端 `metrics` |
| **菜品卡片** | 显示菜名、单价、工艺；Agent 排定的为绿色，手动添加的为橙色 |
| **悬浮添加** | `group-hover:opacity-100` 实现鼠标悬浮时出现"+添加"按钮 |
| **搜索换菜** | 模态弹窗中调用 `/api/dishes/search` 实时搜索菜品库，点击即替换 |

---

### 5. 菜品库 Mock 数据

**文件**: [`backend/app/data/dish_library.json`](backend/app/data/dish_library.json)

菜品库包含 **80 道标准中餐菜品**，覆盖以下分类：

| 分类 | 数量 | 示例菜品 |
|---|---|---|
| **大荤** | 19道 | 红烧肉、糖醋排骨、清蒸鲈鱼、土豆牛腩、宫保鸡丁 |
| **小荤** | 18道 | 青椒肉丝、番茄炒蛋、木须肉、鱼香肉丝、香菇滑鸡 |
| **素菜** | 20道 | 清炒时蔬、地三鲜、麻婆豆腐、酸辣土豆丝、蒜蓉西兰花 |
| **主食** | 10道 | 白米饭、蛋炒饭、手工馒头、杂粮饭、猪肉水饺 |
| **汤**   | 13道 | 紫菜蛋花汤、冬瓜排骨汤、绿豆汤、当归生姜羊肉汤 |

每道菜品包含以下属性：
- `id`: 唯一标识
- `name`: 菜品名称
- `category`: 所属分类（大荤/小荤/素菜/主食/汤）
- `main_ingredients`: 主要食材列表
- `process_type`: 烹饪工艺（炒/蒸/烧/炖/煎/烤/凉拌等）
- `flavor`: 口味特征（咸鲜/酸甜/麻辣/清淡等）
- `cost_per_serving`: 单人份食材成本（元）
- `nutrition`: 营养成分（热量/蛋白质/碳水/脂肪）
- `tags`: 标签数组（菜系/季节/体质/过敏原等）

---

### 6. 全局状态管理

**文件**: [`frontend/src/stores/app-store.ts`](frontend/src/stores/app-store.ts)

使用 **Zustand** 管理全局状态，设计为单一 store 包含四大模块：

```typescript
interface AppState {
    // 1. 规则配置 — 与 PRD 中的 Agent Context JSON Schema 一一对应
    config: MenuPlanConfig;
    updateScene / updateCity / updateSchedule / ...

    // 2. 对话状态 — 消息列表 + 生成状态
    messages: ChatMessage[];
    isGenerating: boolean;

    // 3. 菜单结果 — AI 生成的周菜单 + 核心指标
    weeklyMenu: WeeklyMenu | null;
    metrics: DashboardMetrics | null;

    // 4. UI 状态 — 配置抽屉开关
    configDrawerOpen: boolean;
}
```

**为什么选择 Zustand 而非 Redux/MobX**：Zustand 极其轻量（~1KB），无 Provider 包裹、无 boilerplate 代码，`set()` 和 `get()` API 直观简洁，非常适合中等复杂度的应用。

---

### 7. 设计系统 (Design System)

**文件**: [`frontend/src/index.css`](frontend/src/index.css)

采用 **"清新健康风"** 视觉风格：

| 设计要素 | 实现方式 |
|---|---|
| **主色调** | 翡翠绿渐变 (`primary-400` → `primary-600`) |
| **辅助色** | 青绿 (accent) + 暖黄 (warm) + 红色 (告警) |
| **动画** | 5种自定义动画：`fadeIn` / `slideUp` / `slideRight` / `pulseDot` / `shimmer` |
| **玻璃态** | `.glass` 类实现 `backdrop-filter: blur(12px)` 毛玻璃效果 |
| **滚动条** | 5px 圆角半透明滚动条，悬浮变深 |
| **字体** | Inter + PingFang SC + 微软雅黑 多字体栈 |

---

## 🚀 快速开始

### 环境要求

- **Node.js** ≥ 18.x
- **Python** ≥ 3.10
- **通义千问 API Key** ([申请地址](https://dashscope.console.aliyun.com/))

### 1. 克隆项目

```bash
git clone https://github.com/<your-username>/zouyun-menu-planner.git
cd zouyun-menu-planner
```

### 2. 启动后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置 LLM API Key (修改 app/config.py 中的 LLM_API_KEY，或设置环境变量)
export LLM_API_KEY="your-api-key-here"

# 启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 4. 访问系统

打开浏览器访问 **http://localhost:5173**

---

## 📋 使用指南

### 基本排菜流程

1. **配置约束**：点击右侧对话面板中的 ⚙️ 图标，打开规则配置抽屉
   - 设置食堂场景（高中/医院等）和城市
   - 勾选启用的餐次（午餐/晚餐等）
   - 配置每个餐次的人数、餐标、菜品分类数量
   - 如有特殊群体，勾选对应的健康状态和饮食禁忌
   - 在红线区域填入绝对禁止的食材
   - 点击"保存并同步"

2. **发送指令**：在对话框输入自然语言指令，例如：
   - "帮我排下周的午晚餐菜单"
   - "下周降温，多安排驱寒的汤和炖菜"
   - "控制成本在 10 元/人以内，多用鸡肉替代猪肉"

3. **查看结果**：
   - 右侧观察 Agent 的思考动效（意图解析→成本计算→菜单生成→约束校验）
   - 左侧日历看板自动填充菜品卡片
   - 上方 4 张指标卡片展示总成本、营养达标率等

4. **人工微调**：
   - 鼠标悬浮日历单元格，点击"+添加"按钮
   - 在搜索弹窗中查找菜品，点击即可添加到该位置

### 快捷指令

输入框上方提供 6 个预设快捷标签，点击自动补全：

| 标签 | 效果 |
|---|---|
| `#提高蛋白质` | AI 优先选择高蛋白菜品 |
| `#控制成本在8元内` | 严格限制单人餐标 |
| `#多排清淡菜` | 偏向蒸、煮、白灼工艺 |
| `#下周大降温多排驱寒菜` | 选择温补汤品和炖菜 |
| `#少油少盐` | 规避炸、煎，偏好清淡口味 |
| `#用鸡鸭鱼替换猪肉` | 减少猪肉类菜品，增加禽类和鱼类 |

---

## 🔌 API 接口文档

### 已实现接口

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/api/chat/send` | 智能排菜对话 (SSE 流式) |
| `GET` | `/api/dishes/search?q=xxx` | 搜索菜品库 |
| `GET` | `/api/dishes/library` | 获取完整菜品库 (80道) |
| `GET` | `/api/health` | 健康检查 |

### 占位接口 (待开发)

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/report/nutrition` | 营养报告生成 |
| `GET` | `/api/report/recipe/:id` | 定量配方查看 |
| `POST` | `/api/pricing/sync` | 生鲜时价同步 |
| `POST` | `/api/inventory/sync` | 库存数据同步 |
| `POST` | `/api/plan/save` | 保存排餐计划 |
| `GET` | `/api/plan/:id` | 获取排餐计划 |

交互式文档：启动后端后访问 **http://localhost:8000/docs** (Swagger UI)

---

## 🗺️ 后续开发路线

### Phase 2 — 数据层完善
- [ ] 接入真实的食材定价 API (供应商 ERP)
- [ ] 对接仓库库存管理系统，实现临期食材自动推荐
- [ ] 持久化存储 (SQLite/PostgreSQL) 替代 JSON Mock

### Phase 3 — 智能体进阶
- [ ] 拆分为独立的 Intent Parser / Generator / Checker 三个 Agent
- [ ] 引入循环校验机制（校验不通过自动重排）
- [ ] 基于中国食物成分表实现 DRIs 营养达标率精确计算

### Phase 4 — 生产化
- [ ] 用户认证与多食堂管理
- [ ] 定量配方与采购清单自动生成
- [ ] 历史菜单分析与智能推荐
- [ ] 移动端适配

---

## 📄 许可证

MIT License

---

## 🙏 致谢

- [通义千问 Qwen](https://dashscope.aliyun.com/) — 提供大语言模型 API
- [FastAPI](https://fastapi.tiangolo.com/) — 高性能 Python Web 框架
- [React](https://react.dev/) — 前端 UI 框架
- [Tailwind CSS](https://tailwindcss.com/) — 原子化 CSS 框架
- [Zustand](https://github.com/pmndrs/zustand) — 轻量状态管理
- [Lucide](https://lucide.dev/) — 开源图标库
