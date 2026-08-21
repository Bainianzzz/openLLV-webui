import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    redirect: "/enhance",
  },
  {
    path: "/enhance",
    name: "enhance",
    component: () => import("../pages/EnhancePage.vue"),
    meta: { title: "Enhance" },
  },
  {
    path: "/training",
    name: "training",
    component: () => import("../pages/TrainingPage.vue"),
    meta: { title: "Training" },
  },
  {
    path: "/datasets",
    name: "datasets",
    component: () => import("../pages/DatasetsPage.vue"),
    meta: { title: "Datasets" },
  },
  {
    path: "/tasks",
    name: "tasks",
    component: () => import("../pages/TasksPage.vue"),
    meta: { title: "Tasks" },
  },
  {
    path: "/tasks/:id",
    name: "task-detail",
    component: () => import("../pages/TaskDetailPage.vue"),
    meta: { title: "Task details" },
  },
  {
    path: "/about",
    name: "about",
    component: () => import("../pages/AboutPage.vue"),
    meta: { title: "About" },
  },
];

export default createRouter({
  history: createWebHistory(),
  routes,
});
