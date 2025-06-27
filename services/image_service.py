import os
import uuid
import shutil
import requests
from gradio_client import Client
from config.settings import Config

class ImageService:
    """Service for handling image generation"""
    
    def __init__(self):
        self.gradio_url = Config.GRADIO_CLIENT_URL
        self.client = Client(self.gradio_url) if self.gradio_url else None
        self.output_folder = Config.IMAGE_OUTPUT_FOLDER

    def generate_image(self, prompt):
        """Generate image from text prompt"""
        if not self.client:
            raise ValueError("Gradio client is not initialized")
        
        try:
            result = self.client.predict(prompt=prompt, api_name="/generate")
            print("🔍 Raw result from Gradio:", result)

            # Case 1: Local file path (from Gradio)
            if isinstance(result, str) and os.path.exists(result):
                return self._save_local_image(result)

            # Case 2: URL (future-proofing)
            elif isinstance(result, str) and result.startswith("http"):
                return self._download_and_save_image(result)

            raise ValueError(f"Unexpected API response: {result}")

        except Exception as e:
            raise Exception(f"Image generation failed: {str(e)}")

    def _save_local_image(self, source_path):
        """Save local image file to output folder"""
        ext = os.path.splitext(source_path)[-1]
        filename = f"{uuid.uuid4().hex}{ext}"
        target_path = os.path.join(self.output_folder, filename)
        shutil.copyfile(source_path, target_path)
        return f"/static/generated_images/{filename}"

    def _download_and_save_image(self, url):
        """Download image from URL and save to output folder"""
        img_data = requests.get(url).content
        filename = f"{uuid.uuid4().hex}.png"
        filepath = os.path.join(self.output_folder, filename)
        with open(filepath, 'wb') as f:
            f.write(img_data)
        return f"/static/generated_images/{filename}"