# UI/UX Pro Max 使用手册

> 🎨 专业级 UI/UX 设计智能技能，提供 50+ 设计样式、97 种配色方案、57 种字体搭配和 99 条 UX 指南

---

## 目录

1. [技能概述](#技能概述)
2. [安装验证](#安装验证)
3. [快速开始](#快速开始)
4. [核心功能](#核心功能)
5. [命令详解](#命令详解)
6. [设计系统工作流](#设计系统工作流)
7. [各领域使用指南](#各领域使用指南)
8. [支持的技术栈](#支持的技术栈)
9. [最佳实践](#最佳实践)

---

## 技能概述

**UI/UX Pro Max** 是一个全面的设计智能技能，为 AI 编码助手提供专业级 UI/UX 设计指导。

### 📊 数据库统计

| 类别 | 数量 | 说明 |
|------|------|------|
| 设计样式 | 50+ | 极简主义、玻璃态、新拟态、粗野主义等 |
| 配色方案 | 97 | 按产品类型分类的专业配色 |
| 字体搭配 | 57 | 包含 Google Fonts 导入代码 |
| UX 指南 | 99 | 最佳实践和反模式 |
| 图表类型 | 25 | 数据可视化方案 |
| 技术栈 | 13 | 主流前端框架支持 |

### 🎯 适用场景

- ✅ 设计新的 UI 组件或页面
- ✅ 选择配色方案和字体
- ✅ 审查代码中的 UX 问题
- ✅ 构建落地页或仪表盘
- ✅ 实现无障碍设计要求
- ✅ 优化移动端体验

---

## 安装验证

### 验证安装

```bash
# 测试搜索功能
python "C:\Users\Administrator\.config\opencode\skills\ui-ux-pro-max\scripts\search.py" "minimalism" --domain style -n 3
```

如果看到类似以下输出，说明安装成功：

```
## UI Pro Max Search Results
**Domain:** style | **Query:** minimalism
**Source:** styles.csv | **Found:** 2 results

### Result 1
- **Style Category:** Exaggerated Minimalism
- **Type:** General
...
```

### 安装位置

```
C:\Users\Administrator\.config\opencode\skills\ui-ux-pro-max\
├── data/                 # 设计数据库
│   ├── styles.csv       # 50+ 设计样式
│   ├── colors.csv       # 97 配色方案
│   ├── typography.csv   # 57 字体搭配
│   ├── ux-guidelines.csv # 99 UX 指南
│   └── stacks/          # 技术栈特定指南
├── scripts/             # Python 搜索工具
│   ├── search.py        # 主搜索脚本
│   ├── core.py          # BM25 搜索引擎
│   └── design_system.py # 设计系统生成
└── SKILL.md             # 技能定义文件
```

---

## 快速开始

### 1. 基础搜索

搜索特定领域的设计方案：

```bash
python "C:\Users\Administrator\.config\opencode\skills\ui-ux-pro-max\scripts\search.py" "<关键词>" --domain <领域> [-n <结果数量>]
```

**示例：**
```bash
# 搜索极简主义设计
python "C:\Users\Administrator\.config\opencode\skills\ui-ux-pro-max\scripts\search.py" "minimalism" --domain style

# 搜索 SaaS 配色方案
python "C:\Users\Administrator\.config\opencode\skills\ui-ux-pro-max\scripts\search.py" "saas" --domain color -n 5

# 搜索 UX 最佳实践
python "C:\Users\Administrator\.config\opencode\skills\ui-ux-pro-max\scripts\search.py" "accessibility" --domain ux
```

### 2. 生成完整设计系统

为项目生成综合设计建议：

```bash
python "C:\Users\Administrator\.config\opencode\skills\ui-ux-pro-max\scripts\search.py" "<项目描述>" --design-system -p "项目名称"
```

**示例：**
```bash
# 为美容水疗网站生成设计系统
python "C:\Users\Administrator\.config\opencode\skills\ui-ux-pro-max\scripts\search.py" "beauty spa wellness service" --design-system -p "Serenity Spa"
```

---

## 核心功能

### 功能 1：领域搜索（Domain Search）

在特定设计领域搜索专业建议。

**可用领域：**

| 领域 | 说明 | 示例关键词 |
|------|------|------------|
| `style` | 设计样式 | minimalism, glassmorphism, dark mode |
| `color` | 配色方案 | saas, e-commerce, healthcare |
| `typography` | 字体搭配 | professional, playful, elegant |
| `product` | 产品类型 | dashboard, landing page, portfolio |
| `ux` | UX 最佳实践 | accessibility, animation, forms |
| `chart` | 图表类型 | dashboard, real-time, comparison |
| `landing` | 落地页结构 | saas, product, lead generation |

**命令格式：**
```bash
python scripts/search.py "<关键词>" --domain <领域> [-n <数量>]
```

### 功能 2：技术栈搜索（Stack Search）

获取特定框架的开发指南。

**支持的框架：**
- `html-tailwind` - HTML + Tailwind CSS（默认）
- `react` - React
- `nextjs` - Next.js
- `vue` - Vue.js
- `nuxtjs` - Nuxt.js
- `nuxt-ui` - Nuxt UI
- `svelte` - Svelte
- `astro` - Astro
- `shadcn` - shadcn/ui
- `swiftui` - SwiftUI（iOS）
- `react-native` - React Native
- `flutter` - Flutter
- `jetpack-compose` - Jetpack Compose（Android）

**命令格式：**
```bash
python scripts/search.py "<关键词>" --stack <框架> [-n <数量>]
```

**示例：**
```bash
# 获取 React 样式指南
python "C:\Users\Administrator\.config\opencode\skills\ui-ux-pro-max\scripts\search.py" "glassmorphism" --stack react

# 获取 Next.js 性能优化建议
python "C:\Users\Administrator\.config\opencode\skills\ui-ux-pro-max\scripts\search.py" "performance" --stack nextjs
```

### 功能 3：设计系统生成（Design System）

自动生成包含样式、配色、字体、布局的完整设计系统。

**命令格式：**
```bash
python scripts/search.py "<项目描述>" --design-system [-p "项目名称"]
```

**特点：**
- 并行搜索 5 个领域（产品、样式、配色、落地页、字体）
- 应用智能推理规则选择最佳匹配
- 提供反模式警告
- 包含设计系统变量

### 功能 4：持久化设计系统（Persistence）

保存设计系统以便跨会话使用，支持 Master + Overrides 模式。

**命令格式：**
```bash
# 生成并保存设计系统
python scripts/search.py "<描述>" --design-system --persist -p "项目名称"

# 为特定页面创建覆盖文件
python scripts/search.py "<描述>" --design-system --persist -p "项目名称" --page "dashboard"
```

**生成的文件结构：**
```
design-system/
└── serenity-spa/
    ├── MASTER.md           # 全局设计规范（Source of Truth）
    └── pages/
        └── dashboard.md    # 页面特定覆盖规则
```

**使用流程：**
1. 构建页面时先检查 `pages/[page-name].md`
2. 如果存在，其规则覆盖 MASTER.md
3. 如果不存在，使用 MASTER.md

---

## 命令详解

### 完整命令格式

```bash
python search.py "<查询>" [选项]
```

### 选项说明

| 选项 | 简写 | 说明 | 示例 |
|------|------|------|------|
| `--domain` | `-d` | 搜索领域 | `--domain style` |
| `--stack` | `-s` | 技术栈 | `--stack react` |
| `--max-results` | `-n` | 结果数量 | `-n 5` |
| `--design-system` | `-ds` | 生成设计系统 | `--design-system` |
| `--project-name` | `-p` | 项目名称 | `-p "My Project"` |
| `--persist` | | 持久化设计系统 | `--persist` |
| `--page` | | 页面特定覆盖 | `--page "dashboard"` |
| `--format` | `-f` | 输出格式 | `-f markdown` |
| `--json` | | JSON 输出 | `--json` |

### 使用示例集合

#### 示例 1：样式搜索
```bash
python scripts/search.py "glassmorphism" --domain style -n 3
```

**返回内容包括：**
- 样式类别和关键词
- 主色和次色推荐
- 动画和效果建议
- 适用场景
- AI Prompt 关键词
- CSS 技术关键词
- 实现检查清单
- 设计系统变量

#### 示例 2：配色搜索
```bash
python scripts/search.py "healthcare medical" --domain color -n 3
```

**返回内容包括：**
- 配色方案名称
- 主色、次色、强调色（带色值）
- 使用场景
- 无障碍对比度评级
- 配色策略说明

#### 示例 3：字体搜索
```bash
python scripts/search.py "professional saas" --domain typography
```

**返回内容包括：**
- 字体搭配方案
- Google Fonts 导入代码
- 字体大小和字重建议
- 适用场景

#### 示例 4：UX 指南搜索
```bash
python scripts/search.py "accessibility forms" --domain ux
```

**返回内容包括：**
- UX 规则名称和优先级
- 详细说明
- 代码示例
- 常见错误
- 适用框架

#### 示例 5：图表搜索
```bash
python scripts/search.py "real-time dashboard" --domain chart
```

**返回内容包括：**
- 推荐图表类型
- 适用库（Recharts、Chart.js、D3.js）
- 实现建议
- 无障碍考虑

---

## 设计系统工作流

### 完整工作流程

```
┌─────────────────────────────────────────────────────────────┐
│  步骤 1: 分析需求                                             │
│  - 产品类型（SaaS、电商、作品集等）                            │
│  - 风格关键词（极简、活泼、专业等）                            │
│  - 目标行业（医疗、金融、游戏等）                              │
│  - 技术栈（React、Vue、Tailwind等）                           │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 2: 生成设计系统（必须）                                  │
│  python search.py "<描述>" --design-system -p "项目名"        │
│                                                             │
│  这会并行搜索5个领域：                                        │
│  - 产品类型推荐                                              │
│  - 样式建议                                                  │
│  - 配色方案                                                  │
│  - 落地页结构                                                │
│  - 字体搭配                                                  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 3: 持久化（可选但推荐）                                  │
│  添加 --persist 保存设计系统                                  │
│  添加 --page "<页面名>" 创建页面特定覆盖                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 4: 补充详细搜索                                         │
│  根据需要使用领域搜索获取额外细节                              │
│  python search.py "<关键词>" --domain <领域>                  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 5: 应用设计                                             │
│  使用生成的设计系统变量和指南创建 UI                           │
└─────────────────────────────────────────────────────────────┘
```

### 设计系统输出示例

**生成的设计系统包含：**

```markdown
# 🎨 项目名称 设计系统

## 设计概览
**风格方向:** Minimalism & Swiss Style
**配色基调:** Monochromatic with single accent
**字体氛围:** Clean, professional, highly readable

## 色彩系统
**主色:** #000000 (Black)
**背景:** #FFFFFF (White)
**强调色:** [根据产品类型推荐]

## 字体系统
**标题字体:** Inter / Roboto
**正文字体:** Inter / Open Sans
**导入代码:**
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

## 间距系统
--spacing: 2rem
--section-padding: 4rem
--card-padding: 1.5rem

## 设计系统变量
```css
:root {
  --color-primary: #000000;
  --color-bg: #FFFFFF;
  --spacing: 2rem;
  --border-radius: 0px;
  --shadow: none;
}
```

## 关键原则
1. 充足留白（white space）
2. 清晰的字体层级
3. 网格布局（12-16列）
4. 无装饰性元素
5. WCAG AAA 对比度

## 避免的反模式
❌ 使用阴影和渐变
❌ 过多装饰元素
❌ 不一致的间距
```

---

## 各领域使用指南

### 1. 设计样式（Style）

**搜索命令：**
```bash
python scripts/search.py "<样式名>" --domain style
```

**热门样式：**

| 样式 | 特点 | 适用场景 |
|------|------|----------|
| **Minimalism** | 极简、留白、高对比 | 企业应用、SaaS、仪表盘 |
| **Glassmorphism** | 磨砂玻璃、半透明、模糊背景 | 现代 SaaS、金融仪表盘 |
| **Neumorphism** | 软 UI、浮雕效果 | 健康应用、冥想平台 |
| **Brutalism** | 粗野、高对比、无装饰 | 设计作品集、艺术项目 |
| **Dark Mode** | 深色主题、OLED 优化 | 夜间模式、编码平台 |
| **Bento Grid** | 便当盒布局、卡片网格 | 作品集、产品展示 |

**示例：**
```bash
python scripts/search.py "glassmorphism modern" --domain style -n 3
```

### 2. 配色方案（Color）

**搜索命令：**
```bash
python scripts/search.py "<产品类型>" --domain color
```

**按产品类型搜索：**
```bash
# SaaS 产品
python scripts/search.py "saas b2b" --domain color

# 电商
python scripts/search.py "e-commerce retail" --domain color

# 医疗
python scripts/search.py "healthcare medical" --domain color

# 金融科技
python scripts/search.py "fintech banking" --domain color
```

### 3. 字体搭配（Typography）

**搜索命令：**
```bash
python scripts/search.py "<氛围>" --domain typography
```

**按氛围搜索：**
```bash
# 专业商务
python scripts/search.py "professional corporate" --domain typography

# 活泼创意
python scripts/search.py "playful creative" --domain typography

# 优雅高端
python scripts/search.py "elegant luxury" --domain typography
```

### 4. UX 指南（UX）

**搜索命令：**
```bash
python scripts/search.py "<主题>" --domain ux
```

**常用主题：**
```bash
# 无障碍
python scripts/search.py "accessibility wcag" --domain ux

# 动画
python scripts/search.py "animation micro-interactions" --domain ux

# 表单
python scripts/search.py "forms validation" --domain ux

# 移动端
python scripts/search.py "mobile responsive" --domain ux
```

**UX 规则优先级：**

| 优先级 | 类别 | 重要性 |
|--------|------|--------|
| P1 | 无障碍 (Accessibility) | 🔴 CRITICAL |
| P2 | 触摸与交互 | 🔴 CRITICAL |
| P3 | 性能 | 🟠 HIGH |
| P4 | 布局与响应式 | 🟠 HIGH |
| P5 | 排版与颜色 | 🟡 MEDIUM |
| P6 | 动画 | 🟡 MEDIUM |

### 5. 图表类型（Chart）

**搜索命令：**
```bash
python scripts/search.py "<场景>" --domain chart
```

**示例：**
```bash
# 实时仪表盘
python scripts/search.py "real-time dashboard" --domain chart

# 数据对比
python scripts/search.py "comparison data" --domain chart

# 地理数据
python scripts/search.py "geographic map" --domain chart
```

### 6. 落地页（Landing）

**搜索命令：**
```bash
python scripts/search.py "<类型>" --domain landing
```

**页面类型：**
```bash
# SaaS 落地页
python scripts/search.py "saas product" --domain landing

# 电商转化页
python scripts/search.py "e-commerce conversion" --domain landing

# 潜在客户获取
python scripts/search.py "lead generation" --domain landing
```

---

## 支持的技术栈

### Web 前端

| 框架 | 文件 | 特点 |
|------|------|------|
| **HTML + Tailwind** | `html-tailwind.csv` | 默认推荐，快速原型 |
| **React** | `react.csv` | 组件化开发 |
| **Next.js** | `nextjs.csv` | SSR/SSG 优化 |
| **Vue** | `vue.csv` | 渐进式框架 |
| **Nuxt.js** | `nuxtjs.csv` | Vue 全栈 |
| **Nuxt UI** | `nuxt-ui.csv` | Nuxt 组件库 |
| **Svelte** | `svelte.csv` | 编译时优化 |
| **Astro** | `astro.csv` | 内容驱动 |
| **shadcn/ui** | `shadcn.csv` | Radix + Tailwind |

### 移动端

| 框架 | 文件 | 平台 |
|------|------|------|
| **SwiftUI** | `swiftui.csv` | iOS/macOS |
| **React Native** | `react-native.csv` | 跨平台 |
| **Flutter** | `flutter.csv` | 跨平台 |
| **Jetpack Compose** | `jetpack-compose.csv` | Android |

### 使用技术栈搜索

```bash
# 获取 React 组件最佳实践
python scripts/search.py "component structure" --stack react

# 获取 Tailwind 工具类建议
python scripts/search.py "animation" --stack html-tailwind

# 获取 Next.js 图片优化
python scripts/search.py "image optimization" --stack nextjs
```

---

## 最佳实践

### ✅ 应该做

1. **先生成设计系统**
   ```bash
   python scripts/search.py "<描述>" --design-system -p "项目名"
   ```

2. **持久化设计系统**
   ```bash
   python scripts/search.py "<描述>" --design-system --persist -p "项目名"
   ```

3. **多领域交叉搜索**
   - 样式 + 技术栈
   - 配色 + 产品类型
   - UX + 特定组件

4. **检查反模式**
   - 每个搜索结果都包含"避免使用"
   - 每个设计系统都包含"反模式警告"

5. **使用设计系统变量**
   - 复制生成的 CSS 变量
   - 保持跨页面一致性

### ❌ 不应该做

1. **跳过设计系统生成**
   - 不要直接搜索而不先生成整体设计

2. **忽视无障碍要求**
   - P1/P2 级规则必须遵守
   - 对比度检查不能跳过

3. **混合不兼容的样式**
   - 不要在同一项目中混合多种主要风格

4. **忽视技术栈特定建议**
   - 使用 `--stack` 获取框架特定最佳实践

### 实用技巧

#### 技巧 1：创建快捷方式

在 `.bashrc` 或 `.zshrc` 中添加：
```bash
alias uipm='python "C:\Users\Administrator\.config\opencode\skills\ui-ux-pro-max\scripts\search.py"'
```

使用：
```bash
uipm "minimalism" --domain style
```

#### 技巧 2：保存常用查询

创建 `design-queries.txt`：
```
# SaaS Dashboard
python scripts/search.py "saas dashboard analytics" --design-system -p "MySaaS"

# E-commerce
python scripts/search.py "e-commerce product" --design-system -p "MyShop"

# Portfolio
python scripts/search.py "portfolio creative" --design-system -p "MyPortfolio"
```

#### 技巧 3：结合技术栈和设计

```bash
# 1. 生成设计系统
python scripts/search.py "modern saas" --design-system -p "Project"

# 2. 获取技术栈特定指南
python scripts/search.py "component" --stack react
python scripts/search.py "animation" --stack tailwind

# 3. 检查 UX 要求
python scripts/search.py "accessibility" --domain ux
```

---

## 优先级速查表

### UX 规则优先级（必须遵守）

#### 🔴 CRITICAL - 不可妥协

| 规则 | 要求 | 检查方法 |
|------|------|----------|
| 颜色对比度 | 最小 4.5:1 | WebAIM 对比度检查器 |
| 焦点状态 | 交互元素可见焦点环 | Tab 键测试 |
| 触摸目标 | 最小 44x44px | 开发者工具检查 |
| 表单标签 | 使用 label 和 for 属性 | HTML 验证 |
| 键盘导航 | Tab 顺序匹配视觉顺序 | 键盘测试 |

#### 🟠 HIGH - 强烈推荐

| 规则 | 要求 |
|------|------|
| 图片优化 | WebP 格式、srcset、懒加载 |
| 视口设置 | width=device-width initial-scale=1 |
| 字体大小 | 移动端正文最小 16px |
| Z-index 管理 | 定义规模（10, 20, 30, 50）|

#### 🟡 MEDIUM - 建议实施

| 规则 | 要求 |
|------|------|
| 行高 | 正文 1.5-1.75 |
| 行长度 | 每行 65-75 字符 |
| 动画时长 | 微交互 150-300ms |
| 样式一致性 | 全站使用相同样式 |

---

## 故障排除

### 问题 1：Python 未找到

**错误：**
```
'python' 不是内部或外部命令
```

**解决：**
```bash
# 检查 Python 安装
python3 --version
# 或
python --version

# 如果未安装，下载并安装 Python 3.x
# https://www.python.org/downloads/
```

### 问题 2：编码错误（Windows）

**错误：**
```
UnicodeEncodeError: 'charmap' codec can't encode character
```

**解决：**
脚本已自动处理 UTF-8 编码，通常不需要额外操作。如果仍有问题：
```bash
# 设置 UTF-8 编码
set PYTHONIOENCODING=utf-8
```

### 问题 3：搜索结果为空

**可能原因：**
- 关键词过于具体
- 使用了错误的领域名称

**解决：**
```bash
# 使用更通用的关键词
python scripts/search.py "modern" --domain style

# 检查可用领域
python scripts/search.py --help
```

---

## 总结

**UI/UX Pro Max** 是一个强大的设计智能技能，通过命令行工具提供专业级 UI/UX 指导。

### 核心命令回顾

```bash
# 1. 生成设计系统（开始任何项目的第一步）
python scripts/search.py "<描述>" --design-system -p "项目名"

# 2. 持久化设计系统
python scripts/search.py "<描述>" --design-system --persist -p "项目名" --page "dashboard"

# 3. 领域搜索
python scripts/search.py "<关键词>" --domain <style|color|typography|ux|chart|landing|product>

# 4. 技术栈搜索
python scripts/search.py "<关键词>" --stack <react|vue|nextjs|...>
```

### 记住优先级

1. 🔴 **P1/P2 (CRITICAL)** - 无障碍和交互规则，不可妥协
2. 🟠 **P3/P4 (HIGH)** - 性能和布局，强烈推荐
3. 🟡 **P5-P8 (MEDIUM/LOW)** - 样式和动画，灵活应用

---

**祝你设计愉快！** 🎨✨

如有问题，参考 SKILL.md 文件或重新运行搜索命令。
