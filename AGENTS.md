## 项目开发规则（必须遵守）

- 前端代码位于仓库根目录，Vue/Vite 入口为 `src/`
- 前端组件引用必须优先使用 `@` 路径别名
- 不要自行添加新的前端依赖
- 修改一个包/模块中的代码时，必须先寻找该包及其祖先包/模块中的所有 `README.md` 并阅读
- 不要轻易执行任何项目的构建指令
- 尽量使用 `tailwind-css` 中的预设类型，少用任意值语法或者在 `<style>` 中自定义组件样式

## 技术栈

- Vue 3 + TypeScript，使用 Vite 开发和构建
- Vue Router 负责前端路由，Vitest + jsdom 负责测试
- Tailwind CSS 4，通过 `@tailwindcss/vite` 集成
- 使用 pnpm 管理依赖，版本以 `package.json` 的 `packageManager` 为准

## 项目结构

- `src/main.ts`：应用入口；`src/App.vue`：根组件
- `src/pages/`：页面组件；`src/router/`：路由配置
- `src/components/`：通用 UI 与共享组件
- `src/features/`：按业务域组织的类型、API 和组合式逻辑
- `src/api/`：通用 API 客户端及接口类型
- `src/styles/`：全局样式；`assets/`：静态资源
- `docs/`：重构与架构文档；`.githooks/`：Git hooks
