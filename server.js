const express = require('express');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;

// 静态文件服务
app.use(express.static(path.join(__dirname, 'public')));
app.use('/static', express.static(path.join(__dirname, 'static')));

// API: 获取Hero图片列表
app.get('/api/images/hero', (req, res) => {
  const heroDir = path.join(__dirname, 'static', 'imgs', 'hero');
  try {
    if (fs.existsSync(heroDir)) {
      const files = fs.readdirSync(heroDir)
        .filter(file => /\.(webp|jpg|jpeg|png)$/i.test(file))
        .map(file => `static/imgs/hero/${file}`);
      res.json({ images: files });
    } else {
      res.json({ images: [] });
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// API: 获取Archive结构
app.get('/api/images/archive', (req, res) => {
  const archiveDir = path.join(__dirname, 'static', 'imgs', 'archive');
  const result = {};
  
  try {
    if (fs.existsSync(archiveDir)) {
      // 遍历画幅文件夹
      const formats = fs.readdirSync(archiveDir, { withFileTypes: true })
        .filter(dirent => dirent.isDirectory())
        .map(dirent => dirent.name);
      
      formats.forEach(format => {
        result[format] = {};
        const formatDir = path.join(archiveDir, format);
        
        // 遍历月份文件夹
        const months = fs.readdirSync(formatDir, { withFileTypes: true })
          .filter(dirent => dirent.isDirectory())
          .map(dirent => dirent.name);
        
        months.forEach(month => {
          const monthDir = path.join(formatDir, month);
          const files = fs.readdirSync(monthDir)
            .filter(file => /\.(webp|jpg|jpeg|png)$/i.test(file))
            .map(file => `static/imgs/archive/${format}/${month}/${file}`);
          
          result[format][month] = {
            cover: files.find(f => f.includes('cover')) || files[0] || null,
            images: files
          };
        });
      });
    }
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 主页
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// 启动服务器
app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
