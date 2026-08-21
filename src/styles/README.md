# 样式系统

本模块维护全局 CSS、Tailwind CSS 4 入口和应用设计令牌。项目使用 CSS-first 配置，没有 `tailwind.config` 文件。

## `app.css`

- 通过 `@import "tailwindcss"` 和 `@import "tw-animate-css"` 加载工具类与动画。
- 在 `:root` 和 `.dark` 中定义 shadcn-vue 风格的 HSL 语义变量。
- 使用 `@theme inline` 将变量映射为 Tailwind 颜色、字号、字距和圆角工具类。
- 提供基础 border、页面高度、背景、前景色和系统字体设置。

项目额外定义了 `text-2xs`、`text-3xs`、`tracking-caps`、`tracking-label`、`tracking-eyebrow` 和 `tracking-display` 等令牌。优先复用这些令牌，不要用任意值复制相同尺寸。

## 约定

- 跨页面设计令牌和确需全局生效的 CSS 放在本目录。
- 页面和组件使用 Tailwind 工具类，不添加带实际样式内容的 `<style>` 块。
- UI 原语优先使用 `background`、`foreground`、`primary`、`muted` 等语义颜色，避免绕过主题变量。
- 修改语义变量时同时验证其前景色配对和 `.dark` 定义。
