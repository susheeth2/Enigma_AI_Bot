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
        self.output_folder = Config.IMAGE_OUTPUT_FOLDER
        self.client = None

        # Ensure output folder exists
        os.makedirs(self.output_folder, exist_ok=True)

        # Try to initialize Gradio client
        try:
            if self.gradio_url:
                self.client = Client(self.gradio_url)
                print(f"✅ Gradio client initialized at {self.gradio_url}")
            else:
                print("⚠️ Gradio URL not provided.")
        except Exception as e:
            print(f"❌ Failed to initialize Gradio client: {e}")

    def generate_image(self, prompt):
        """Generate image from text prompt"""
        if not self.client:
            print("⚠️ Gradio client is not available. Skipping image generation.")
            return None  # or raise a custom warning if needed

        try:
            result = self.client.predict(prompt=prompt, api_name="/generate")
            print("🔍 Raw result from Gradio:", result)

            # Case 1: Local file path
            if isinstance(result, str) and os.path.exists(result):
                return self._save_local_image(result)

            # Case 2: Remote URL
            elif isinstance(result, str) and result.startswith("http"):
                return self._download_and_save_image(result)

            raise ValueError(f"Unexpected API response: {result}")

        except Exception as e:
            print(f"❌ Image generation failed: {e}")
            return None

    def _save_local_image(self, source_path):
        """Save local image file to output folder"""
        ext = os.path.splitext(source_path)[-1]
        filename = f"{uuid.uuid4().hex}{ext}"
        target_path = os.path.join(self.output_folder, filename)
        shutil.copyfile(source_path, target_path)
        return f"/static/generated_images/{filename}"

    def _download_and_save_image(self, url):
        """Download image from URL and save to output folder"""
        try:
            response = requests.get(url)
            response.raise_for_status()
            filename = f"{uuid.uuid4().hex}.png"
            filepath = os.path.join(self.output_folder, filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return f"/static/generated_images/{filename}"
        except Exception as e:
            print(f"❌ Failed to download image from URL: {e}")
            return None
