# 仓库管理系统（多团队隔离）

这是一个基于 Django + DRF + JWT 的仓库管理系统，支持。
-
本系统起初是想为我的家人开发，随后便结合trea一起打造，适合小规模公司仓库管理，水平差不多也就是中国大学生毕业实际水平吧，如果你有需要使用，可以在我的基础上继续修改。

- 团队号登录：同团队共享数据、不同团队数据隔离
- 团队注册：创建团队 + 首个账号自动成为管理员
- 账号管理：管理员可创建/删除成员账号
- 操作日志：记录关键操作用于审计

## 目录说明

- `warehouse_system/`：项目配置（settings/urls/wsgi/asgi）
- `users/`：团队、账号、登录、审计日志
- `products/`：商品
- `inventory/`：库存
- `records/`：入库/出库记录（含导出）
- `analytics_app/`：统计分析
- `templates/`：前端页面模板
- `static/`：静态资源（CSS/JS/echarts 等）

## 环境要求

- Python 3.8+（建议 3.10+）
- MySQL 5.7/8.0

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置（推荐用 .env）

项目会自动读取项目根目录下的 `.env` 文件（如果存在）。

示例（按需修改）：

```env
# 运行环境
DEBUG=False
DJANGO_SECRET_KEY=请换成你自己的随机长字符串
ALLOWED_HOSTS=你的域名,你的服务器IP
CSRF_TRUSTED_ORIGINS=https://你的域名,https://你的服务器IP

# 数据库（MySQL）
USE_MYSQL=True
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=warehouse_system
MYSQL_USER=wms_user
MYSQL_PASSWORD=123456

# 可选（HTTPS/反代场景）
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=0
SECURE_HSTS_INCLUDE_SUBDOMAINS=False
SECURE_HSTS_PRELOAD=False
X_FRAME_OPTIONS=DENY
```

关键说明：

- 线上务必 `DEBUG=False`，并设置 `DJANGO_SECRET_KEY`、`ALLOWED_HOSTS`。
- 如果你使用域名 + HTTPS，建议设置 `CSRF_TRUSTED_ORIGINS`。

## 初始化数据库

```bash
python manage.py migrate
```

如需后台管理账号：

```bash
python manage.py createsuperuser
```

## 本地启动

```bash
python manage.py runserver 0.0.0.0:8000
```

浏览器访问：

- `http://127.0.0.1:8000/`（前端页面）
- `http://127.0.0.1:8000/admin/`（Django 后台）

## 登录与团队

- 登录必须提供：团队号（team\_code）+ 用户名 + 密码
- 注册团队：会创建一个新团队，并把第一个账号设置为管理员
- 管理员可以在“账号管理”页面创建/删除成员账号

## 主要接口（后端）

- `POST /api/auth/register/`：注册团队 + 创建管理员账号
- `POST /api/auth/login/`：登录（JWT），需携带 `team_code`
- `POST /api/auth/refresh/`：刷新 token
- `GET /api/auth/me/`：当前用户信息（含团队与管理员标识）
- `GET/POST/DELETE /api/auth/team/subaccounts/`：团队成员管理（管理员权限）
- `GET /api/auth/audit-logs/`：团队审计日志（最近 100 条）

