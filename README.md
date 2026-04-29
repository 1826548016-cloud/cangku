# 智能仓库管理系统（WMS）
项目更在更新目前有较大漏洞 不要直接采纳




基于 Django、Django REST Framework、JWT 和 ECharts 的智能仓库管理系统，适用于商品、库存、出入库记录和数据分析的一体化管理。

## 已实现功能

- JWT 登录、刷新、当前用户信息获取
- 单端登录控制，同一账号在其他设备登录后旧会话自动失效
- 商品新增、修改、删除，支持商品图片上传与预览
- 库存查询与预警值修改
- 入库、出库登记
- 出库前库存校验，防止负库存
- 删除入库/出库记录时自动回滚库存
- 出入库记录支持按 SKU、商品名称、备注搜索
- 出入库记录 PDF 导出
- 数据分析面板，包含近 7 天趋势、库存预警对比、分类占比、热销商品排行
- 前端单页控制台，支持移动端访问
- 当前登录用户动态水印

## 技术栈

- 后端：Django、Django REST Framework、Simple JWT
- 数据库：MySQL
- 前端：HTML、CSS、JavaScript、ECharts
- 报表：ReportLab

## 快速启动

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

浏览器访问 `http://127.0.0.1:8000/`，使用创建的账号登录。

## MySQL 配置

项目默认读取根目录 `.env` 文件中的数据库配置，示例：

```env
USE_MYSQL=True
MYSQL_DATABASE=warehouse_system
MYSQL_USER=wms_user
MYSQL_PASSWORD=123456
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
```

请先在 MySQL 中创建数据库并确保用户有访问权限，然后执行：

```bash
python manage.py migrate
```

如需参考，可复制 `.env.example` 为 `.env` 后再按本机环境修改。

## 主要接口

### 认证

- `POST /api/auth/login/`
- `POST /api/auth/refresh/`
- `GET /api/auth/me/`

### 商品与库存

- `GET|POST /api/products/`
- `GET|PATCH|DELETE /api/products/<id>/`
- `GET|PATCH /api/inventory/<id>/`

### 出入库记录

- `GET|POST /api/records/stockin/`
- `GET|POST /api/records/stockout/`
- `DELETE /api/records/stockin/<id>/`
- `DELETE /api/records/stockout/<id>/`
- `GET /api/records/stockin/export/pdf/`
- `GET /api/records/stockout/export/pdf/`

### 数据分析

- `GET /api/analytics/`

## 目录结构

```text
cangku/
├── analytics_app/
├── inventory/
├── products/
├── records/
├── users/
├── static/
├── templates/
├── media/
├── .env.example
├── manage.py
└── requirements.txt
```
