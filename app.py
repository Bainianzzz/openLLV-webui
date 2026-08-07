"""Thin entry point for the openLLV Gradio web UI."""

from ui import build

if __name__ == "__main__":
    demo = build()
    demo.queue()
    demo.launch()
