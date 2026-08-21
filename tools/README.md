# 自定义检查工具

本目录维护项目本地的 ESLint、Stylelint 规则及其测试，用于表达通用规则集无法覆盖的前端约束。

## 新增或修改规则

1. 在对应工具目录实现规则，并导出便于单元测试的纯函数。
2. 添加或更新同目录的 `*.test.mjs`。
3. 在根目录 `eslint.config.mjs` 或 `stylelint.config.mjs` 中注册并限定作用范围。
4. 运行 `pnpm test`、`pnpm lint` 和 `pnpm lint:styles` 验证规则及集成。

Vitest 通过 `vite.config.ts` 收集 `tools/**/*.test.mjs`。修改 AST 或文件匹配行为时应补充相应测试覆盖。
