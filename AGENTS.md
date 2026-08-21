## 项目开发规则（必须遵守）

- 前端组件引用必须优先使用 `@` 路径别名
- 不要自行使用 `pnpm` 添加新的前端依赖，必须告知用户并在用户同意后添加或管理依赖
- 修改一个包/模块中的代码前，必须从仓库根目录到目标目录依次寻找并阅读沿途所有 `README.md`，以了解逐层收窄的架构边界和模块约定
- 代码变更导致关联的 README 中的职责、依赖、接口或约定失效时，必须在同一任务中同步更新；新增复杂模块时应补充 README
- 不要轻易执行任何项目的构建指令
- 不要随意使用 `eslint-disable` 或 `stylelint-disable` 豁免检查；确实需要豁免时，必须向用户报告豁免位置、规则名称和原因
- 在完成一个阶段所有编码任务后，运行 `pnpm lint` 和 `pnpm lint:styles` 检查代码是否符合项目规范，根据警告适当修改，以代码可读性和逻辑性为先，不用完全采纳
- 添加新的 eslint 或 stylelint 后，需要补充测试

## 技术栈

- Vue 3 + TypeScript，使用 Vite 开发和构建，使用 `vue-tsc` 做类型检查
- Vue Router 使用 history 模式和路由级懒加载；应用状态由页面和业务组合式函数管理，当前未引入全局 Store
- Axios 负责 HTTP 请求，统一复用 `src/api/http.ts` 中以 `/api/v1` 为前缀的实例
- Tailwind CSS 4 通过 `@tailwindcss/vite` 和 CSS-first 配置集成；本地 UI 原语采用 shadcn-vue 风格，并使用 Reka UI、CVA、clsx 和 tailwind-merge
- Vitest + jsdom + Vue Test Utils 负责组合式函数与工具测试
- ESLint 和 Stylelint 当前主要承载 `tools/` 中的项目自定义规则，Prettier 负责 `src/` 格式化
- 使用 pnpm 管理依赖，版本以 `package.json` 的 `packageManager` 为准

## 项目结构

- `src/main.ts`：应用入口；`src/App.vue`：根组件
- `src/router/`：history 模式路由、根路径重定向和路由页面懒加载
- `src/pages/`：增强、训练、数据集、任务和项目说明等路由页面
- `src/components/shared/`：应用外壳和页面级共享展示组件；`src/components/ui/`：本地维护的 shadcn-vue 风格 UI 原语
- `src/features/`：数据集、训练和任务领域的有状态组合式逻辑；增强流程当前仍由页面直接编排
- `src/api/`：共享 Axios 实例、各领域请求封装和响应归一化
- `src/types/`：服务端请求响应契约、任务可判别联合和前端归一化视图类型
- `src/lib/`：底层共享工具，当前提供 Tailwind class 合并函数
- `src/styles/`：Tailwind CSS 入口、全局样式和设计令牌；根目录 `assets/`：示例图片资源
- `tools/`：自定义 ESLint、Stylelint 规则及测试
- `docs/`：openLLV-server API 文档索引；`.githooks/`：按暂存文件范围运行测试的 Git hooks
