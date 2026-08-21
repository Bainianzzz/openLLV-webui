# openLLV WebUI

Vue frontend for the openLLV enhancement, training, and dataset workflows.

## 快速开始

```bash
pnpm install
pnpm dev
```

The backend is maintained in the separate `openLLV-server` repository.

## 代码检查

```bash
pnpm lint
pnpm lint:styles
```

Tailwind 任意值检查规则位于 `tools/eslint/`，组件自定义 CSS 检查规则位于
`tools/stylelint/`。全局样式放在 `src/styles/`，组件和页面优先使用 Tailwind
class。
