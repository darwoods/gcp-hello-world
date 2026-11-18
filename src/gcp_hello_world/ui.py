import gradio as gr
from .logic import generate_greeting

def build_gradio_app() -> gr.Blocks:
    def on_click(name: str) -> str:
        result = generate_greeting(name)
        return f"{result['message']} (Server time: {result['timestamp']})"

    with gr.Blocks(title="Cloud Run Gradio UI") as demo:
        gr.Markdown("## Cloud Run Gradio Test")
        name_input = gr.Textbox(label="Name", placeholder="World")
        btn = gr.Button("Generate Greeting", variant="primary")
        output = gr.Textbox(label="Server Response", interactive=False)
        
        btn.click(fn=on_click, inputs=name_input, outputs=output)
        
    return demo