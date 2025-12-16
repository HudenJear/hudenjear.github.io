# Reversal & Chrome - Slide Film Archive

一个基于 Node.js 的摄影作品集网站，专注于反转片（E-6 Slide Film）的展示与归档，并支持为每张照片维护“底片是否已售”的状态。

## 技术栈

- **后端**: Node.js 20 LTS + Express
- **前端**: 原生 HTML/CSS/JavaScript
- **图片处理**: Python + Pillow

## 项目结构

```
├── public/                  # 静态前端文件
│   ├── index.html          # 主页面
│   ├── photo.html          # 图片详情页
│   ├── styles.css          # 主样式
│   └── photo.css           # 详情页样式
├── static/imgs/
│   ├── photos/             # 所有图片统一存储（原比例）
│   │   ├── 6x6_2024-12_001.webp
│   │   └── ...
│   └── manifest.json       # 图片元数据索引
├── data/
│   └── comments/           # 评论数据（每张图片一个json）
│       ├── 6x6_2024-12_001.json
│       └── ...
│   └── sale-list.json       # 底片出售状态（每张图片一条记录）
├── server.js               # Express 服务器
├── package.json            # Node.js 配置
├── .nvmrc                  # Node 版本指定
├── process_images.py       # 图片处理脚本
├── update_sale_list.py      # 更新 sale-list.json 的脚本（首次会自动创建）
└── requirements.txt        # Python 依赖
```

## 快速开始

### 1. 环境要求

- Node.js >= 20.0.0
- Python >= 3.8（用于图片处理）

### 2. 安装依赖

```bash
# 克隆仓库
apt install npm
apt install python3-pip
git clone https://github.com/HudenJear/hudenjear.github.io.git
cd hudenjear.github.io

# 安装 Node.js 依赖
npm install

# 安装 Python 依赖（用于图片处理）
pip install -r requirements.txt
```

### 3. 准备图片

创建源图片文件夹，结构如下：

```
E:\个人主页图片文件夹\        # 或你自定义的路径
├── archive/                 # 归档图片（主要图片来源）
│   ├── 6x6/                # 胶片画幅
│   │   ├── 2024-12/        # 月份
│   │   └── 2024-11/
│   ├── 6x7/
│   └── 35mm/
├── hero.txt                 # 标记哪些图片用于Hero（可选）
├── filmlab/
├── prints/
└── common/
```

**hero.txt 格式**（每行一个图片ID，可选文件）：
```
6x6_2024-12_001
6x7_2024-11_003
```
如果不创建此文件，所有archive图片都会作为Hero候选。

### 4. 处理图片

修改 `process_images.py` 中的 `source_path` 变量为你的源图片路径，然后运行：

```bash
python process_images.py
```

脚本会自动：
- 将所有图片统一存储到 `static/imgs/photos/` 目录
- 保持原比例，长边不超过 1800px
- 转换为 WebP 格式
- 生成 `manifest.json` 索引文件

### 5. 启动服务器

```bash
# 开发环境
npm run dev

# 生产环境
npm start
```

访问 http://localhost:3000

## 生产环境部署

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

```bash
nginx -t
nginx -s reload
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/manifest` | GET | 获取图片索引 manifest.json |
| `/api/photo/:id` | GET | 获取单张图片元数据 |
| `/api/comments/:photoId` | GET | 获取指定图片的评论 |
| `/api/comments/:photoId` | POST | 提交评论（需要email、content） |

## manifest.json 结构

```json
{
  "version": "2.0",
  "photos": {
    "6x6_2024-12_001": {
      "id": "6x6_2024-12_001",
      "file": "photos/6x6_2024-12_001.webp",
      "format": "6x6",
      "date": "2024-12",
      "width": 1200,
      "height": 1200,
      "tags": ["archive", "hero"]
    }
  },
  "indexes": {
    "hero": ["6x6_2024-12_001", ...],
    "archive": {
      "6x6": { "2024-12": [...], "2024-11": [...] },
      "6x7": {...}
    }
  }
}
```

## 图片存储方案

- **统一存储**: 所有图片存储在 `static/imgs/photos/` 目录
- **原比例保存**: 长边不超过 1800px，保持原始比例
- **前端裁剪**: Hero/Highlights/Archive 使用 CSS `object-fit: cover` 裁剪为正方形
- **详情页原图**: photo.html 展示原比例图片

## 功能特性

- **Hero 轮播**: 展示精选作品，每日随机排序，CSS裁剪为正方形
- **Highlights**: 每日从 Hero 中随机抽选 2 张展示
- **Archive**: 按胶片画幅（6x6、6x7、35mm）和月份分类归档
- **图片详情页**: 展示原图、Archive信息、摄影师信息
- **评论系统**: 文件存储（每张图片一个json），按图片ID独立管理，需邮箱验证
- **响应式设计**: 适配桌面和移动设备

## License

MIT
