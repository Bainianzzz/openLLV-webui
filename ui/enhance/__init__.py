"""Enhancement UI package: traditional and deep-learning sections."""

from __future__ import annotations

from pathlib import Path

import gradio as gr

from inference.enhance import available_enhancers


def method_choices(rows) -> list[str]:
    """Turn ``llv.list_available()`` rows into Gradio dropdown choices."""
    return sorted(row["name"] for row in rows)


def example_images() -> list[str]:
    """Resolve bundled example images relative to the project root."""
    assets = Path(__file__).resolve().parents[2] / "assets"
    examples = []
    for name in ("input.jpg", "input2.jpg", "input3.jpg"):
        path = assets / name
        if path.is_file():
            examples.append(str(path))
    return examples


def image_display() -> tuple[gr.Image, gr.Image]:
    """Build the shared input/output image display and examples."""
    with gr.Row():
        image = gr.Image(
            type="pil",
            label="Input Image",
            sources=["upload", "clipboard"],
            height=480,
            width=480,
        )
        output = gr.Image(
            type="pil",
            label="Enhanced Result",
            height=480,
            width=480,
        )

    return image, output


def build_enhance() -> dict:
    """Assemble the traditional and deep-learning sections as tabs."""
    from .deep_learning import build_deep_learning_section
    from .traditional import build_traditional_section

    enhancers = available_enhancers()
    with gr.Tabs():
        with gr.Tab("Traditional Algorithm"):
            traditional = build_traditional_section(enhancers)
        with gr.Tab("Deep Learning Model"):
            deep_learning = build_deep_learning_section(enhancers)

    return {
        "traditional": traditional,
        "deep_learning": deep_learning,
    }


__all__ = ["build_enhance"]
