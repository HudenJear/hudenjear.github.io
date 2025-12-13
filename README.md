# Capture & Collect - Photography Portfolio

一个基于 Node.js 的摄影作品集网站，支持胶片摄影作品的展示与归档。

## 技术栈

- **后端**: Node.js 20 LTS + Express
- **前端**: 原生 HTML/CSS/JavaScript
- **图片处理**: Python + Pillow

## 项目结构

```
├── public/                  # 静态前端文件
│   ├── index.html          # 主页面
│   └── styles.css          # 样式文件
├── static/                  # 图片资源
│   └── imgs/
│       ├── hero/           # Hero轮播图片
│       ├── archive/        # 归档图片（按画幅/月份分类）
│       │   ├── 6x6/
│       │   │   ├── 2024-12/
│       │   │   └── ...
│       │   ├── 6x7/
│       │   └── 35mm/
│       ├── filmlab/
│       ├── prints/
│       └── common/
├── server.js               # Express 服务器
├── package.json            # Node.js 配置
├── .nvmrc                  # Node 版本指定
├── process_images.py       # 图片处理脚本
└── requirements.txt        # Python 依赖
```

## 快速开始

### 1. 环境要求

- Node.js >= 20.0.0
- Python >= 3.8（用于图片处理）

### 2. 安装依赖

```bash
# 安装 Node.js 依赖
npm install

# 安装 Python 依赖（用于图片处理）
pip install -r requirements.txt
```

### 3. 准备图片

创建源图片文件夹，结构如下：

```
E:\个人主页图片文件夹\        # 或你自定义的路径
├── hero/                    # Hero轮播图片
├── archive/                 # 归档图片
│   ├── 6x6/                # 胶片画幅
│   │   ├── 2024-12/        # 月份
│   │   └── 2024-11/
│   ├── 6x7/
│   └── 35mm/
├── filmlab/
├── prints/
└── common/
```

### 4. 处理图片

修改 `process_images.py` 中的 `source_path` 变量为你的源图片路径，然后运行：

```bash
python process_images.py
```

脚本会自动：
- 创建目标文件夹结构
- 调整图片尺寸
- 转换为 WebP 格式
- 输出到 `static/imgs/` 目录

### 5. 启动服务器

```bash
# 开发环境
npm run dev

# 生产环境
npm start
```

访问 http://localhost:3000

## 生产环境部署

### 方式一：PM2 部署

```bash
# 安装 PM2
npm install -g pm2

# 启动服务
pm2 start server.js --name "portfolio"

# 设置开机自启
pm2 startup
pm2 save
```

### 方式二：配置 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 静态资源缓存
    location /static {
        proxy_pass http://127.0.0.1:3000/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

### 方式三：Docker 部署

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY . .
EXPOSE 3000
CMD ["node", "server.js"]
```

```bash
# 构建镜像
docker build -t portfolio .

# 运行容器
docker run -d -p 3000:3000 --name portfolio portfolio
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/images/hero` | GET | 获取 Hero 图片列表 |
| `/api/images/archive` | GET | 获取 Archive 结构（画幅/月份） |

## 图片尺寸配置

| 分类 | 尺寸 | 说明 |
|------|------|------|
| hero | 800×800 | 正方形，1:1 比例 |
| archive | 120×120 | 缩略图 |
| filmlab | 400×530 | 竖向 |
| prints | 400×530 | 竖向 |

## 功能特性

- **Hero 轮播**: 展示精选作品，每日随机排序
- **Highlights**: 每日从 Hero 中随机抽选 2 张展示
- **Archive**: 按胶片画幅（6x6、6x7、35mm）和月份分类归档
- **响应式设计**: 适配桌面和移动设备

## License

MIT
