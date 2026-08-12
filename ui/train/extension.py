"""Extension components: optional SwanLab experiment recording."""

from __future__ import annotations

import gradio as gr

from inference import config, project_url


def _open_project(api_key: str, project: str) -> dict:
    """Return the project-jump button state for the given SwanLab settings.

    The runtime key/project override the ``config.yaml`` values in memory
    (the same way ``run_training`` does), so the button always points at the
    account the next training run will record to. An empty key or a failed
    lookup disables the button with a hint instead of an error.
    """
    config().set_swanlab_api_key(api_key)
    config().set_swanlab_project(project)
    if not config().swanlab_api_key:
        return {"value": "Enter an API key", "link": None, "interactive": False}
    try:
        url = project_url()
    except Exception:  # noqa: BLE001 - an unreachable/invalid key disables the button
        return {
            "value": "Could not resolve project link",
            "link": None,
            "interactive": False,
        }
    return {"value": "Open project", "link": url, "interactive": True}


def build_extension_section() -> dict:
    """Create the extension components (SwanLab API key and project).

    When the key is filled in, training runs through
    ``BatchSwanLabTrainer`` and the session is recorded in the given project
    in SwanLab. The boxes are pre-filled with the ``config.yaml`` values so
    a configured key/project shows up without re-entering them. The button
    next to the title opens the recorded project; it refreshes whenever the
    key or project changes.
    """
    initial = _open_project(
        config().swanlab_api_key or "",
        config().swanlab_project or "",
    )
    with gr.Column():
        with gr.Row():
            gr.Markdown("## SwanLab")
            open_project = gr.Button(
                value=initial["value"],
                link=initial["link"],
                link_target="_blank",
                interactive=initial["interactive"],
                scale=0,
            )
        api_key = gr.Textbox(
            label="API Key",
            type="password",
            value=config().swanlab_api_key or "",
        )
        project = gr.Textbox(
            label="Project",
            placeholder="openLLV",
            value=config().swanlab_project or "",
        )

    api_key.change(fn=_open_project, inputs=[api_key, project], outputs=[open_project])
    project.change(fn=_open_project, inputs=[api_key, project], outputs=[open_project])

    return {"api_key": api_key, "project": project, "open_project": open_project}


__all__ = ["build_extension_section"]
