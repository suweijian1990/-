# Design

## Color Strategy

**Restrained** — 语义优先，强调色仅用于主要操作和状态指示

## Color Palette

### Primary (品牌色)
- **用途**: 主要按钮、链接、活跃状态、焦点指示器
- **色值**: `#2563eb` (靛蓝)
- **选择理由**: 专业、可信赖、科技感，与 Notion/Linear 风格一致

### Neutrals (中性色)
采用带微蓝调的灰色系，与品牌色协调

| Token | 色值 | 用途 |
|-------|------|------|
| `--ink` | `#0f172a` | 主文字 |
| `--ink-secondary` | `#334155` | 次要文字 |
| `--ink-muted` | `#64748b` | 辅助文字、标签 |
| `--ink-faint` | `#94a3b8` | 占位符、禁用状态 |
| `--border` | `#e2e8f0` | 边框、分隔线 |
| `--border-hover` | `#cbd5e1` | hover 边框 |
| `--surface` | `#ffffff` | 卡片、面板背景 |
| `--surface-raised` | `#f8fafc` | 次级表面 |
| `--bg` | `#f1f5f9` | 页面背景 |
| `--bg-hover` | `#e2e8f0` | hover 背景 |

### Semantic (语义色)

| 语义 | 色值 | 用途 |
|------|------|------|
| Success | `#059669` | 成功状态、确认操作 |
| Error | `#dc2626` | 错误、删除操作 |
| Warning | `#d97706` | 警告、需要注意 |
| Info | `#2563eb` | 信息提示（与主色相同） |

## Typography

- **字体**: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif
- **主文字**: 15px, 重量 400-600
- **标题**: 1.25rem, 重量 700
- **辅助**: 0.85rem, 重量 400

## Components

### 按钮
- **Primary**: `#2563eb` 背景，白色文字，8px 圆角
- **Secondary**: 白色背景，`#d1d5db` 边框，深色文字
- **Danger**: `#dc2626` 背景，白色文字

### 卡片
- 白色背景，`#e2e8f0` 边框，12px 圆角
- 微弱阴影: `0 1px 2px rgba(0,0,0,0.04)`

### 表格
- 表头: `#f8fafc` 背景，`#64748b` 文字
- 行: 白色背景，hover 时 `#f8fafc`
- 边框: `#f1f5f9`

### 侧边栏
- 背景: `#0f172a` (深色)
- 文字: `rgba(255,255,255,0.65)`
- 活跃项: `#2563eb` 背景

## Layout

- **侧边栏宽度**: 260px
- **内容区 padding**: 32px
- **卡片间距**: 20px
- **圆角**: 8-12px

## Motion

- **过渡时间**: 0.15-0.2s ease
- **Hover 效果**: 轻微上浮、阴影增强
- **不使用**: 弹性动画、复杂过渡
