from backend.db import Task

from test.helpers import database_session


def test_task_list_detail_and_cancel(client, session_factory, supervisor):
    with database_session(session_factory) as session:
        session.add(Task(id="task-1", kind="training", status="running", message="Training is running"))

    listed = client.get("/api/v1/tasks", params={"kind": "training"})
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == "task-1"

    detail = client.get("/api/v1/tasks/task-1")
    assert detail.status_code == 200
    assert detail.json()["status"] == "running"

    cancelled = client.post("/api/v1/tasks/task-1/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelling"
    assert supervisor.cancelled == [("task-1", "training")]


def test_missing_task_uses_standard_error_shape(client):
    response = client.get("/api/v1/tasks/missing")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "task_not_found"
    assert response.json()["error"]["request_id"]
