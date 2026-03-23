# 阶段一：构建 React 应用
FROM node:18-alpine AS builder

WORKDIR /app

# 复制 package 文件并安装依赖
COPY package*.json ./
RUN npm ci

# 复制源代码并执行生产构建
COPY . .
RUN npm run build

# 阶段二：使用 Nginx 提供服务并配置反向代理
FROM nginx:alpine

# 清理默认静态文件
RUN rm -rf /usr/share/nginx/html/*

# 复制构建产物至 Nginx 静态目录
COPY --from=builder /app/dist /usr/share/nginx/html

# 覆盖默认的 Nginx 配置，以便支持前端路由并反向代理 /api 到后端
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
