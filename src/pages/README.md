# 路由页面

本模块包含应用的路由级 Vue 页面。路由表位于 `@/router`，页面通过动态导入懒加载，并由 `AppShell` 内的 `RouterView` 渲染。

## 页面与路由

| 路由 | 页面 | 职责 |
| --- | --- | --- |
| `/enhance` | `EnhancePage.vue` | 上传图片、配置并跟踪增强任务 |
| `/training` | `TrainingPage.vue` | 配置并跟踪模型训练 |
| `/datasets` | `DatasetsPage.vue` | 下载和管理数据集 |
| `/tasks` | `TasksPage.vue` | 筛选、分页和查看任务列表 |
| `/tasks/:id` | `TaskDetailPage.vue` | 查看任务详情和取消任务 |
| `/about` | `AboutPage.vue` | 展示项目说明 |

根路径重定向到 `/enhance`。路由使用 `createWebHistory`，部署环境需要 SPA history fallback。

## 页面边界

- 页面负责布局、展示和用户事件组合；可复用的异步业务状态应放入 `@/features`。
- 服务端请求必须通过 `@/api`，不要在页面中直接使用 Axios。
- 通用页面结构使用 `@/components/shared`，基础交互和视觉元素使用 `@/components/ui`。
- 跨目录引用优先使用 `@` 别名。
- 页面和组件中不添加 `<style>` 内容，样式使用 Tailwind 工具类或维护在全局样式模块中。
