import gradio as gr
import logging
import tempfile
import os
from qrxfer.generator import QRVideoGenerator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_file(file):
    if file is None:
        return None, "Please select a file to convert."
    
    try:
        logger.info(f"Processing file: {file.name}")
        
        output_dir = tempfile.mkdtemp()
        output_video = os.path.join(output_dir, "qr_video.mp4")
        
        generator = QRVideoGenerator(qr_version=40, qr_size=400, fps=25, num_processes=4)
        generator.generate(file.name, output_video)
        
        logger.info(f"Video generated successfully: {output_video}")
        return output_video, "Video generated successfully!"
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return None, error_msg

with gr.Blocks(title="QR Code Video Generator") as app:
    gr.Markdown("# QR Code Video Generator")
    
    with gr.Row():
        file_input = gr.File(label="Select File", file_count="single")
        video_output = gr.Video(label="Generated Video")
    
    status_text = gr.Textbox(label="Status", interactive=False)
    
    submit_btn = gr.Button("Generate QR Video", variant="primary")
    
    submit_btn.click(
        fn=process_file,
        inputs=file_input,
        outputs=[video_output, status_text]
    )
    

if __name__ == "__main__":
    app.launch()

