# UI 组件

本目录维护项目本地拥有的 UI 原语，结构遵循 shadcn-vue 风格并由根目录 `components.json` 描述。组件源码属于本项目，不应把它们视为不可修改的第三方包。

## 依赖

- Reka UI 提供 Select、Checkbox、ToggleGroup 和 ScrollArea 等无样式可访问性原语。
- `class-variance-authority` 管理 Button、Badge 等组件的 variant。
- `clsx` 与 `tailwind-merge` 由 `@/lib/utils` 的 `cn` 统一封装。
- Tailwind CSS 4 和 `src/styles/app.css` 提供工具类、语义颜色与尺寸令牌。
- `@lucide/vue` 提供图标，`tw-animate-css` 提供全局动画工具类。

## 约定

- 每组组件使用独立目录和 `index.ts` 导出，调用方通过 `@/components/ui/<name>` 引用。
- 可接收样式的组件将调用方传入的 `class` 与默认类通过 `cn` 合并。
- 复合原语必须保留正确结构，例如 Select 的 root、trigger、content 和 item。
- Reka UI 包装组件需要正确转发 attributes、model 和插槽；设置 `inheritAttrs: false` 时必须显式绑定 `$attrs`。
- 视觉颜色优先使用 `bg-background`、`text-foreground` 等语义令牌。
- 不添加组件 `<style>` 内容。自定义 Stylelint 规则要求组件样式使用 Tailwind 或全局样式。
- 优先使用 Tailwind 预设工具类，并通过自定义 ESLint 规则检查任意值的使用。

修改或重新生成组件时，应检查本地 variant、属性转发和导出文件，避免生成器覆盖项目已有调整。跨目录引用优先使用 `@` 别名。
