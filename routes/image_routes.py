from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify, send_from_directory
from services.image_service import ImageService
from config.settings import Config

image_bp = Blueprint('image', __name__)
image_service = ImageService()

@image_bp.route('/image_generator')
def image_generator():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('img_gen.html', username=session['username'])

@image_bp.route("/generate", methods=["POST"])
def generate_image():
    print("✅ Reached /generate endpoint")
    data = request.get_json()
    prompt = data.get("prompt")

    try:
        image_url = image_service.generate_image(prompt)
        return jsonify({"image_url": image_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@image_bp.route('/static/generated_images/<filename>')
def serve_image(filename):
    return send_from_directory(Config.IMAGE_OUTPUT_FOLDER, filename)