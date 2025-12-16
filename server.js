const express = require('express');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;

// 路径配置
const DATA_DIR = path.join(__dirname, 'data');
const COMMENTS_DIR = path.join(DATA_DIR, 'comments');
const MANIFEST_PATH = path.join(__dirname, 'static', 'imgs', 'manifest.json');
const SALE_LIST_PATH = path.join(DATA_DIR, 'sale-list.json');
const LEGACY_MANIFESTATION_DIR = path.join(__dirname, 'manifestation');
const LEGACY_SALE_LIST_PATH = path.join(LEGACY_MANIFESTATION_DIR, 'sale-list.json');

// 确保data目录存在
if (!fs.existsSync(DATA_DIR)) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}

// 确保comments目录存在（每张图片一个json文件）
if (!fs.existsSync(COMMENTS_DIR)) {
  fs.mkdirSync(COMMENTS_DIR, { recursive: true });
}

// 兼容迁移：如果旧的 manifestation/sale-list.json 存在而新的 data/sale-list.json 不存在，则复制过去
try {
  if (!fs.existsSync(SALE_LIST_PATH) && fs.existsSync(LEGACY_SALE_LIST_PATH)) {
    fs.copyFileSync(LEGACY_SALE_LIST_PATH, SALE_LIST_PATH);
  }
} catch {
  // ignore
}

function isSafePhotoId(photoId) {
  return typeof photoId === 'string' && /^[a-zA-Z0-9_-]+$/.test(photoId);
}

function getCommentsFilePath(photoId) {
  return path.join(COMMENTS_DIR, `${photoId}.json`);
}

function readComments(photoId) {
  const filePath = getCommentsFilePath(photoId);
  if (!fs.existsSync(filePath)) return [];

  const raw = fs.readFileSync(filePath, 'utf8');
  const data = JSON.parse(raw);
  if (!Array.isArray(data)) return [];
  return data;
}

function writeComments(photoId, comments) {
  const filePath = getCommentsFilePath(photoId);
  fs.writeFileSync(filePath, JSON.stringify(comments, null, 2));
}

function readSaleList() {
  if (!fs.existsSync(SALE_LIST_PATH)) {
    return { version: '1.0', updatedAt: new Date().toISOString(), sales: {} };
  }

  const raw = fs.readFileSync(SALE_LIST_PATH, 'utf8');
  const data = JSON.parse(raw);
  if (!data || typeof data !== 'object') {
    return { version: '1.0', updatedAt: new Date().toISOString(), sales: {} };
  }

  if (!data.sales || typeof data.sales !== 'object') {
    data.sales = {};
  }

  return data;
}

function getSoldStatus(photoId) {
  try {
    const saleList = readSaleList();
    const rec = saleList.sales?.[photoId];
    if (typeof rec === 'boolean') return rec;
    if (rec && typeof rec === 'object' && rec.sold === true) return true;
    return false;
  } catch {
    return false;
  }
}

// 中间件
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));
app.use('/static', express.static(path.join(__dirname, 'static')));

// API: 获取manifest.json
app.get('/api/manifest', (req, res) => {
  try {
    if (fs.existsSync(MANIFEST_PATH)) {
      const manifest = JSON.parse(fs.readFileSync(MANIFEST_PATH, 'utf8'));
      res.json(manifest);
    } else {
      res.status(404).json({ error: 'manifest.json not found' });
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// API: 获取单张图片信息
app.get('/api/photo/:id', (req, res) => {
  try {
    if (!fs.existsSync(MANIFEST_PATH)) {
      return res.status(404).json({ error: 'manifest.json not found' });
    }
    
    const manifest = JSON.parse(fs.readFileSync(MANIFEST_PATH, 'utf8'));
    const photoId = req.params.id;
    const photo = manifest.photos[photoId];
    
    if (photo) {
      const sold = getSoldStatus(photoId);
      res.json({ ...photo, id: photoId, sold });
    } else {
      res.status(404).json({ error: 'Photo not found' });
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// API: 获取指定图片的评论（按图片ID单独存储）
app.get('/api/comments/:photoId', (req, res) => {
  const photoId = req.params.photoId;
  if (!isSafePhotoId(photoId)) {
    return res.status(400).json({ error: 'Invalid photoId' });
  }

  try {
    const comments = readComments(photoId)
      .slice()
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    res.json({ comments });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// API: 提交评论
app.post('/api/comments/:photoId', (req, res) => {
  const { email, name, content } = req.body;
  const photoId = req.params.photoId;

  if (!isSafePhotoId(photoId)) {
    return res.status(400).json({ error: 'Invalid photoId' });
  }
  
  // 验证必填字段
  if (!email || !content) {
    return res.status(400).json({ error: '缺少必填字段（邮箱和内容）' });
  }
  
  // 邮箱格式验证
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    return res.status(400).json({ error: '邮箱格式不正确' });
  }

  try {
    const comments = readComments(photoId);
    const comment = {
      id: Date.now().toString(),
      photo_id: photoId,
      email,
      name: name || 'Anonymous',
      content,
      created_at: new Date().toISOString()
    };
    comments.push(comment);
    writeComments(photoId, comments);

    res.json({ success: true, comment });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 图片详情页
app.get('/photo', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'photo.html'));
});

app.get('/reversal-intro', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'reversal-intro.html'));
});

app.get('/film-library', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'film-library.html'));
});

app.get('/film', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'film.html'));
});

app.get('/highlights', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'highlights.html'));
});

app.get('/archive', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'archive.html'));
});

app.get('/archive-month', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'archive-month.html'));
});

// 主页
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// 启动服务器
app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
