import { defineComponent } from "vue";
import { mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { TaskDetail } from "./types";
import { getTask, listTasks } from "./api";
import { useTasks } from "./useTasks";

vi.mock("./api", () => ({ cancelTask: vi.fn(), getTask: vi.fn(), listTasks: vi.fn() }));

const mockedGetTask = vi.mocked(getTask);
const mockedListTasks = vi.mocked(listTasks);

function detail(status: TaskDetail["status"]): TaskDetail {
  return {
    id: "task-1",
    kind: "training",
    status,
    message: null,
    created_at: "2026-01-01T00:00:00Z",
    started_at: null,
    finished_at: null,
    training: {},
    job: {},
    error_code: null,
    error_detail: null,
  } as TaskDetail;
}

let composable: ReturnType<typeof useTasks>;

function mountTasks() {
  return mount(
    defineComponent({
      setup() {
        composable = useTasks();
        return {};
      },
      template: "<div />",
    }),
  );
}

beforeEach(() => {
  vi.useFakeTimers();
  mockedGetTask.mockReset();
  mockedListTasks.mockReset();
});

afterEach(() => vi.useRealTimers());

describe("useTasks", () => {
  it("stops polling when the task is terminal", async () => {
    mockedGetTask.mockResolvedValue(detail("succeeded"));
    const wrapper = mountTasks();

    await composable.loadTask("task-1");

    expect(mockedGetTask).toHaveBeenCalledTimes(1);
    expect(vi.getTimerCount()).toBe(0);
    wrapper.unmount();
  });

  it("polls a non-terminal task until the next result is terminal", async () => {
    mockedGetTask.mockResolvedValueOnce(detail("running")).mockResolvedValueOnce(detail("failed"));
    const wrapper = mountTasks();

    await composable.loadTask("task-1");
    expect(vi.getTimerCount()).toBe(1);
    await vi.advanceTimersByTimeAsync(2000);

    expect(mockedGetTask).toHaveBeenCalledTimes(2);
    expect(vi.getTimerCount()).toBe(0);
    wrapper.unmount();
  });

  it("does not let an older detail request clear loading for a newer request", async () => {
    let resolveFirst!: (value: TaskDetail) => void;
    let resolveSecond!: (value: TaskDetail) => void;
    const first = new Promise<TaskDetail>((resolve) => {
      resolveFirst = resolve;
    });
    const second = new Promise<TaskDetail>((resolve) => {
      resolveSecond = resolve;
    });
    mockedGetTask.mockReturnValueOnce(first).mockReturnValueOnce(second);
    const wrapper = mountTasks();

    const firstLoad = composable.loadTask("first", false);
    const secondLoad = composable.loadTask("second", false);
    resolveFirst(detail("succeeded"));
    await firstLoad;
    expect(composable.detailLoading.value).toBe(true);
    resolveSecond(detail("succeeded"));
    await secondLoad;
    expect(composable.detailLoading.value).toBe(false);
    wrapper.unmount();
  });

  it("aborts requests and clears polling on unmount", async () => {
    mockedGetTask.mockResolvedValue(detail("running"));
    const wrapper = mountTasks();

    await composable.loadTask("task-1");
    const signal = mockedGetTask.mock.calls[0]?.[1];
    expect(signal?.aborted).toBe(false);
    expect(vi.getTimerCount()).toBe(1);

    wrapper.unmount();

    expect(signal?.aborted).toBe(true);
    expect(vi.getTimerCount()).toBe(0);
  });
});
