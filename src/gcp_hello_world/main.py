# A simple Cloud Run hybrid demo

import gradio as gr
from fastapi import FastAPI
from .logic import generate_greeting
from .ui import build_gradio_app

app = FastAPI(title="Cloud Run Hybrid Test")

@app.get("/")
async def root():
    return {
        "status": "running",
        "try_api": "/api/greet?name=Developer",
        "try_swagger_docs": "/docs",
        "try_gradio_ui": "/ui",
    }

@app.get("/api/greet")
async def api_greet(name: str = "World"):
    return generate_greeting(name)

# Mount the Gradio interface at /ui
gradio_app = build_gradio_app()
app = gr.mount_gradio_app(app, gradio_app, path="/ui")