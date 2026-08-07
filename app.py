"""Thin entry point for the openLLV Gradio web UI."""

from inference import init_db
from ui import build

if __name__ == "__main__":
    init_db()
    demo = build()
    demo.queue().launch()
