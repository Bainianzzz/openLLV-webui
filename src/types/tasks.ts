import type {
  Page,
  TaskDetail,
  TaskKind,
  TaskStatus,
  TaskSummary,
} from "@/types";

export type { TaskDetail, TaskKind, TaskStatus, TaskSummary };
export type TaskPage = Page<TaskSummary>;
export interface TaskListParams {
  page?: number;
  page_size?: number;
  kind?: TaskKind;
  status?: TaskStatus;
  created_after?: string;
  created_before?: string;
}
