import base64
from io import BytesIO
from flask import Flask, request, jsonify
from flask_cors import CORS
from diffusers import StableDiffusionPipeline
import torch
from dotenv import load_dotenv
import requests
import os

# Initialize Flask app and enable CORS
app = Flask(__name__)
CORS(app)

# Load environment variables from .env file
load_dotenv()

# API Key for Gemini
GEMINI_API_KEY = os.getenv('gemini_api_key')

# Load Stable Diffusion model
def load_pipeline():
    """
    Load the Stable Diffusion pipeline for image generation.
    """
    model_id = "dreamlike-art/dreamlike-diffusion-1.0"
    pipe = StableDiffusionPipeline.from_pretrained(
        model_id,
        torch_dtype=torch.float16,
        use_safetensors=True
    )
    return pipe.to("cuda")

# Load the model at startup
pipe = load_pipeline()

@app.route('/generate-blog', methods=['POST'])
def generate_blog():
    """
    Generate a blog using the Gemini API.
    """
    try:
        # Parse input data
        input_data = request.json
        title = input_data.get("title", "")
        keywords = input_data.get("keywords", "")
        wordlimit = input_data.get("wordlimit", 250)

        # Validate inputs
        if not title or not keywords or wordlimit <= 0:
            return jsonify({"error": "Invalid input fields"}), 400

        # Construct prompt for the API
        prompt = (
            f"Generate a Comprehensive, Engaging Blog relevant to this title: {title} "
            f"and these keywords: {keywords}, without exceeding {wordlimit} words."
        )

        # API request payload
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        }

        # Define API URL and headers
        headers = {'Content-Type': 'application/json'}
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

        # Make API call
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()

        # Return the generated blog content
        return jsonify(response_data), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate-image', methods=['POST'])
def generate_image():
    """
    Generate images using the Dreamlike Diffusion model.
    """
    try:
        # Parse input data
        input_data = request.json
        title = input_data.get("title", "")
        num_images = input_data.get("images", 1)
        img_prompt = f"Generate a Blog Post Image using the title: {title}"

        # Validate inputs
        if not title or num_images <= 0:
            return jsonify({"error": "Invalid input fields"}), 400

        # Generate images
        images = []
        for _ in range(num_images):
            image = pipe(img_prompt).images[0]
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)
            base64_image = base64.b64encode(buffer.read()).decode()
            images.append(f"data:image/png;base64,{base64_image}")

        # Return the generated images in base64 format
        return jsonify({"images": images}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

app.run(host='0.0.0.0', port=5000)
