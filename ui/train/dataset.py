"""Dataset selection components: pick a dataset and its local root."""

from __future__ import annotations

import gradio as gr

from . import name_choices


def build_dataset_section(datasets: list) -> dict:
    """Create the dataset-selection components.

    Picks a registered dataset (e.g. CommonDataset) and the local root that
    training reads from; the download section fills this path automatically.
    """
    choices = name_choices(datasets)

    with gr.Column():
        dataset = gr.Dropdown(choices=choices, value=choices[0], label="Dataset")
        root_dir = gr.Textbox(
            label="Local Path",
            placeholder="path/to/dataset; filled by Download or typed manually",
        )

    return {"dataset": dataset, "root_dir": root_dir}
