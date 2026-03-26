# FastAPI 后台项目结构 + 数据表设计

目标是做一个 **DCDeepTech API Gateway MVP**：

- 前端：`platform.dcdeeptech.com`
- 后端：`api.dcdeeptech.com`
- 能注册 / 登录
- 能生成 API key
- 能调用 `/v1/chat/completions`
- 能记录 usage
- 能做余额扣费
- 能给管理员看用户和日志

---

## 1）推荐技术栈

### 后端
- **FastAPI**
- Python 3.11
- Uvicorn

### 数据库
- **PostgreSQL**

### ORM
- **SQLAlchemy 2.0** + Alembic

### 认证
- 用户登录：JWT
- API 调用：Bearer API key

### 配置
- Pydantic Settings

### 可选
- Redis（后面做限流 / 缓存）
- httpx（转发上游请求）

---

## 2）推荐目录结构

```text
dcdeeptech-api/
├─ app/
│  ├─ main.py
│  ├─ core/
│  │  ├─ config.py
│  │  ├─ security.py
│  │  ├─ database.py
│  │  └─ deps.py
│  ├─ models/
│  │  ├─ user.py
│  │  ├─ api_key.py
│  │  ├─ model_catalog.py
│  │  ├─ wallet.py
│  │  ├─ transaction.py
│  │  └─ usage_log.py
│  ├─ schemas/
│  │  ├─ auth.py
│  │  ├─ user.py
│  │  ├─ api_key.py
│  │  ├─ model_catalog.py
│  │  ├─ wallet.py
│  │  ├─ usage.py
│  │  └─ chat.py
│  ├─ api/
│  │  ├─ auth.py
│  │  ├─ users.py
│  │  ├─ api_keys.py
│  │  ├─ models.py
│  │  ├─ usage.py
│  │  ├─ billing.py
│  │  ├─ admin.py
│  │  └─ openai_proxy.py
│  ├─ services/
│  │  ├─ auth_service.py
│  │  ├─ api_key_service.py
│  │  ├─ wallet_service.py
│  │  ├─ usage_service.py
│  │  ├─ pricing_service.py
│  │  ├─ provider_router.py
│  │  └─ openai_proxy_service.py
│  ├─ adapters/
│  │  ├─ openrouter_adapter.py
│  │  ├─ vllm_adapter.py
│  │  └─ base.py
│  └─ utils/
│     ├─ time.py
│     ├─ idgen.py
│     └─ masking.py
├─ alembic/
├─ tests/
├─ .env
├─ requirements.txt
└─ README.md
```

---

## 3）核心数据表设计

### 表 1：users

```sql
users
- id                    uuid pk
- email                 varchar unique not null
- password_hash         varchar not null
- full_name             varchar null
- role                  varchar not null default 'user'   -- user/admin
- status                varchar not null default 'active' -- active/disabled/pending
- company_name          varchar null
- country               varchar null
- created_at            timestamptz not null
- updated_at            timestamptz not null
- last_login_at         timestamptz null
```

用途：
- 平台账号主体
- 管理员也是 user，只是 role 不同

---

### 表 2：api_keys

```sql
api_keys
- id                    uuid pk
- user_id               uuid fk -> users.id
- name                  varchar not null
- key_prefix            varchar not null
- key_hash              varchar not null
- status                varchar not null default 'active'  -- active/revoked
- created_at            timestamptz not null
- last_used_at          timestamptz null
- expires_at            timestamptz null
```

说明：
- **不要存完整明文 key**
- 只在创建时返回一次，例如：
  `dcdt_sk_live_xxxxxxxxx`
- 数据库只存：
  - `key_prefix`
  - `key_hash`

---

### 表 3：model_catalog

```sql
model_catalog
- id                    uuid pk
- public_name           varchar unique not null
- provider              varchar not null          -- openrouter / vllm / dahua / custom
- upstream_model        varchar not null
- modality              varchar not null default 'text'   -- text/vision
- input_price_per_1k    numeric(18,8) not null default 0
- output_price_per_1k   numeric(18,8) not null default 0
- enabled               boolean not null default true
- is_public             boolean not null default true
- created_at            timestamptz not null
- updated_at            timestamptz not null
```

用途：
- 前端 `/v1/models` 列表
- 做价格映射
- 做路由映射

例子：

- `gpt-4.1`
- `claude-3.7-sonnet`
- `qwen2.5-72b-instruct`
- `deepseek-r1`
- `qwen2.5-vl-72b`

---

### 表 4：wallets

```sql
wallets
- id                    uuid pk
- user_id               uuid fk -> users.id unique
- balance               numeric(18,6) not null default 0
- currency              varchar not null default 'USD'
- updated_at            timestamptz not null
```

用途：
- 用户余额
- MVP 先做预充值扣费模型

---

### 表 5：transactions

```sql
transactions
- id                    uuid pk
- user_id               uuid fk -> users.id
- type                  varchar not null        -- topup/debit/refund/manual_adjustment
- amount                numeric(18,6) not null
- currency              varchar not null default 'USD'
- reference_type        varchar null            -- usage/order/manual
- reference_id          varchar null
- description           varchar null
- created_by_user_id    uuid null
- created_at            timestamptz not null
```

用途：
- 所有余额变化流水
- 后台手工加款 / 扣款都记这里

---

### 表 6：usage_logs

```sql
usage_logs
- id                    uuid pk
- request_id            varchar unique not null
- user_id               uuid fk -> users.id
- api_key_id            uuid fk -> api_keys.id
- model_name            varchar not null
- provider              varchar not null
- upstream_model        varchar not null
- prompt_tokens         integer not null default 0
- completion_tokens     integer not null default 0
- total_tokens          integer not null default 0
- cost_input            numeric(18,8) not null default 0
- cost_output           numeric(18,8) not null default 0
- total_cost            numeric(18,8) not null default 0
- latency_ms            integer null
- status_code           integer not null
- success               boolean not null default true
- client_ip             varchar null
- error_message         text null
- created_at            timestamptz not null
```

用途：
- 计费
- 仪表盘 usage 图
- 管理员审计

---

## 4）核心业务流程

### A. 注册登录流程
1. 用户注册
2. 存 `users`
3. 初始化 `wallets`
4. 登录成功后返回 access token

### B. API key 创建流程
1. 用户登录
2. 点 “Create Key”
3. 后端生成明文 key
4. 数据库存 hash
5. 返回一次完整 key 给前端
6. 后续只显示 prefix

### C. Chat Completions 调用流程
1. 客户端请求 `POST /v1/chat/completions`
2. 校验 Bearer API key
3. 找到用户 + key 状态
4. 检查模型是否 enabled
5. 检查余额是否足够
6. 路由到对应 provider
7. 拿到返回结果
8. 提取 usage
9. 计算成本
10. 扣余额
11. 写 `usage_logs`
12. 返回 OpenAI-compatible 响应

### D. 管理员调余额流程
1. admin 登录
2. 选用户
3. 输入加款金额
4. 更新 `wallets.balance`
5. 写 `transactions`

---

## 5）接口设计

### 认证

#### `POST /auth/register`
请求：

```json
{
  "email": "user@example.com",
  "password": "StrongPassword123",
  "full_name": "Test User"
}
```

返回：

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "role": "user",
  "status": "active"
}
```

#### `POST /auth/login`
请求：

```json
{
  "email": "user@example.com",
  "password": "StrongPassword123"
}
```

返回：

```json
{
  "access_token": "jwt_token",
  "token_type": "bearer"
}
```

#### `GET /auth/me`

### API Keys

#### `GET /v1/keys`
返回当前用户所有 key

#### `POST /v1/keys`
请求：

```json
{
  "name": "Production Key"
}
```

返回：

```json
{
  "id": "uuid",
  "name": "Production Key",
  "key": "dcdt_sk_live_xxxxxxxxxxxxx",
  "key_prefix": "dcdt_sk_live_xxx",
  "created_at": "..."
}
```

#### `DELETE /v1/keys/{id}`
软删除 / revoke

### Models

#### `GET /v1/models`
返回平台开放模型

### Wallet & Billing

#### `GET /v1/wallet`
#### `GET /v1/usage`
支持按日期筛选
#### `GET /v1/billing/transactions`

### OpenAI-Compatible Proxy

#### `POST /v1/chat/completions`

请求例子：

```json
{
  "model": "gpt-4.1",
  "messages": [
    { "role": "user", "content": "Hello" }
  ],
  "temperature": 0.7
}
```

返回尽量兼容 OpenAI 格式。

### Admin

#### `GET /admin/users`
#### `GET /admin/usage`
#### `POST /admin/wallets/{user_id}/adjust`
请求：

```json
{
  "amount": 50.0,
  "description": "Manual top-up"
}
```

#### `POST /admin/models`
#### `PATCH /admin/models/{id}`

---

## 6）配置文件建议

`.env`

```env
APP_NAME=DCDeepTech API Gateway
APP_ENV=dev
SECRET_KEY=change_me
ACCESS_TOKEN_EXPIRE_MINUTES=10080

DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/dcdeeptech
CORS_ORIGINS=https://platform.dcdeeptech.com,http://localhost:5173

OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

DEFAULT_CURRENCY=USD
```

---

## 7）关键安全要求

### 用户密码
- bcrypt / argon2 hash
- 不存明文

### API key
- 只显示一次完整值
- 数据库存 hash
- 支持 revoke

### 管理员接口
- 必须检查 `role == admin`

### CORS
- 只允许：
  - `https://platform.dcdeeptech.com`
  - 本地开发地址

### 日志
- 不要打印密码
- 不要打印完整 API key
- 不要打印上游敏感 token

---

## 8）MVP 优先级

### 第一周必须做
- auth
- api_keys
- `/v1/models`
- `/v1/chat/completions`
- usage_logs
- wallet
- admin 调余额

### 第二周再做
- 用户分页
- 日志筛选
- 请求限流
- 充值订单
- 邮件通知
