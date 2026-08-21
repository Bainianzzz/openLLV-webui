## 项目开发规则（必须遵守）

- 前端组件引用必须优先使用 `@` 路径别名
- 不要自行使用 `pnpm` 添加新的前端依赖，必须告知用户并在用户同意后添加或管理依赖
- 修改一个包/模块中的代码时，必须先寻找该包及其祖先包/模块中的所有 `README.md` 并阅读
- 不要轻易执行任何项目的构建指令
- 不要随意使用 `eslint-disable` 或 `stylelint-disable` 豁免检查；确实需要豁免时，必须向用户报告豁免位置、规则名称和原因
- 在完成一个阶段所有编码任务后，运行 `pnpm lint` 和 `pnpm lint:styles` 检查代码是否符合项目规范，根据警告适当修改，以代码可读性和逻辑性为先，不用完全采纳
- 添加新的 eslint 或 stylelint 后，需要补充测试

## 技术栈

- Vue 3 + TypeScript，使用 Vite 开发和构建
- Vue Router 负责前端路由；Vitest + jsdom 负责测试
- Axios 负责 HTTP 请求，统一通过 `src/api/http.ts` 配置
- Tailwind CSS 4，通过 `@tailwindcss/vite` 集成
- ESLint、Stylelint 和 Prettier 负责代码规范与格式化
- 使用 pnpm 管理依赖，版本以 `package.json` 的 `packageManager` 为准

## 项目结构

- `src/main.ts`：应用入口；`src/App.vue`：根组件
- `src/pages/`：页面组件；`src/router/`：路由配置
- `src/components/`：通用 UI 与共享组件
- `src/features/`：按业务域组织的组合式逻辑
- `src/api/`：HTTP 实例和所有 API 请求模块
- `src/types/`：API 与业务类型定义
- `src/styles/`：全局样式；`assets/`：静态资源
- `tools/`：自定义 ESLint、Stylelint 规则及测试
- `docs/`：重构与架构文档；`.githooks/`：Git hooks
