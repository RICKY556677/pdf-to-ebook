# PDF-to-Ebook Skill

将英文 PDF 翻译为中文并生成精致排版 PDF 电子书的完整工作流。

## 触发条件

- 用户上传英文 PDF 并要求翻译成中文电子书
- 用户说"把这个 PDF 做成中文电子书"、"翻译这份 PDF 并排版"
- 任何涉及 PDF → 中文精排电子书的需求

## 工作流（4 阶段）

### 阶段 1：PDF 文本提取（确保高成功率）

按以下优先级依次尝试，每次尝试后检查结果完整性：

**优先级 1 — `pdf` 工具（内置）**
```
用 pdf 工具逐页提取全部文字。记录哪些页提取成功、哪些失败。
```

**优先级 2 — `pdftotext`（poppler）**
```
如果内置 pdf 工具有页面失败：
1. brew install poppler（如果未安装，等待最多 120s）
2. pdftotext -layout input.pdf output.txt
3. 检查失败页面是否被提取
```

**优先级 3 — PyMuPDF（Python）**
```
如果 pdftotext 也不完整：
1. pip3 install PyMuPDF（等待最多 120s）
2. 用 Python 脚本逐页提取：
   import fitz
   doc = fitz.open(pdf_path)
   for page in doc:
       print(page.get_text())
3. 检查失败页面
```

**优先级 4 — 图片 OCR（针对图片化页面）**
```
如果仍有页面是图片格式无法提取文字：
1. pip3 install PyMuPDF（如未安装）
2. 将失败页面导出为 PNG（用 PyMuPDF 的 page.get_pixmap()）
3. 用 autoglm-image-recognition skill 逐张 OCR
4. 合并 OCR 结果
```

**兜底方案 — 请求用户协助**
```
如果以上全部失败或某个方法超时（>120s）：
→ 告诉用户哪些页面无法提取
→ 请用户用 Preview 打开 PDF → 文件 → 导出为文本
→ 或用截图工具截取失败页面发给 Agent OCR
```

**⚠️ 关键原则：** 每个方法尝试不超过 1 次，安装命令超时 120s 即跳过。不在同一个方法上反复重试。优先用 `pdf` 工具（最快），逐级降级。

### 阶段 2：翻译

1. 将提取的英文文本完整保存为 `original.md`
2. 逐章翻译为中文，保存为 `translated.md`
3. 翻译要求：
   - 术语保留英文原文（如 MVP、PMF、CAC、LTV、GTM）
   - 保持原文的强调（加粗）、列表、引用结构
   - 表格完整翻译
   - 章节标题格式：`# 第X章 中文标题`
   - 附录标题：`# 附录：中文标题`
4. 如果原文内容超过 20 页，分批翻译，每批保存追加

### 阶段 3：排版生成

使用项目内置的 `build_pdf.py` 脚本生成 HTML 和 PDF：

```
python3 build_pdf.py
```

脚本会自动：
- 解析 Markdown 的章节结构
- 生成封面页（暖米色背景，书名+副标题+出处）
- 生成目录页（独立一页，点状引导线连接章节名）
- 每个章节生成独立标题页（暖米色背景+金色竖线装饰）
- 正文使用白色底色，统一 2.8cm 页边距

如果脚本不在当前目录，从 skill 目录复制：
```
cp ~/.openclaw-autoclaw/skills/pdf-to-ebook/build_pdf.py ./
```

### 阶段 4：PDF 导出

1. 用 Python HTTP Server 托管 HTML：
   ```
   python3 -m http.server 8765 -d <output_dir> &
   ```
2. 用 `browser` 工具打开 `http://localhost:8765/<filename>.html`
3. 用 `browser action=pdf` 导出 PDF
4. 复制到目标位置（如桌面）

## 输出物

| 文件 | 说明 |
|------|------|
| `original.md` | 原始英文文本 |
| `translated.md` | 中文翻译 |
| `<书名>.html` | 精排 HTML |
| `<书名>.pdf` | 最终 PDF 电子书 |

## 注意事项

- 安装命令（brew/pip）超时 120s 直接跳过，不反复重试
- PDF 提取阶段遇到连续的图片化页面（如 InDesign 导出的后半部分），直接用优先级 4 或兜底方案
- 翻译时保留英文术语，不强行翻译专业名词
- PDF 导出前确保关闭 Preview 进程（`osascript -e 'tell application "Preview" to quit'`）避免文件锁定
