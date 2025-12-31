# 部署指南 (Deployment Guide)

## 快速开始

### 1. 首次部署 (First Time Deploy)
运行以下命令构建并启动所有服务（前端、后端、数据库）：

```bash
make deploy
```
> **注意**：首次运行时，数据库会自动初始化。

### 2. 更新代码 (Update Code)
当你修改了前端或后端代码，想要快速上线测试时，请运行：

```bash
make update
```
此命令只会重新构建并重启应用服务，**不会影响数据库**。

### 3. 查看日志 (View Logs)
如果遇到问题，可以查看实时日志：
```bash
make logs
```

### 4. 首次启动与管理员账号
项目启动后，系统会自动检测是否存在管理员账号。如果没有，将自动创建一个默认管理员：
- **用户名**: `admin`
- **密码**: `admin`

请在首次登录后尽快更改密码。

### 5. 停止服务 (Stop Services)
```bash
make deploy-down
```

---

## 架构说明 (Architecture)

- **Frontend (Nginx)**: 前端容器内置了 Nginx，监听端口 `80` (映射到主机的 `8090`，即访问 `http://localhost:8090`)。
  - 它处理静态页面请求。
  - 它将 `/api` 请求反向代理给后端容器。
- **Backend**: Python/FastAPI 服务，仅在容器网络内部暴露，不直接对外。
- **Database**: Postgres 数据库。

## ⚠️ 重要注意事项 (Important Notes)

### 1. 数据持久化 (Data Persistence)
- 数据库文件存储在 Docker Volume `postgres_data` 中。
- **安全的操作**：`make deploy`, `make update`, `make deploy-down` 都是安全的，不会丢失数据。
- **危险的操作**：`make clean` 或 `docker-compose down -v` 会**删除数据卷**，导致数据永久丢失！

### 2. Nginx 配置
- Nginx 配置文件位于 `frontend/nginx.conf`。
- 如果你需要修改反向代理规则，修改该文件后运行 `make update` 即可生效。

### 3. 生产环境安全
- 请务必修改 `docker-compose.prod.yml` 中的 `SECRET_KEY` 和数据库密码。
- 确保防火墙只开放必要的端口（如 80/443）。
