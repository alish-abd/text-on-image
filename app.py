from flask import Flask, request, send_file, jsonify
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

app = Flask(__name__)

# Logo URL (Replace with your own logo URL)
LOGO_URL = "https://i.postimg.cc/xjb5Lpdm/Group-73.png"

@app.route('/')
def home():
    return "Flask Image Editor is running!"

@app.route('/edit_image', methods=['POST'])
def edit_image():
    try:
        # Get JSON data from request
        data = request.get_json()
        image_url = data.get("image_url")
        text = data.get("text", "Default Text")

        # Download the image
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))

        # Download the logo
        logo_response = requests.get(LOGO_URL)
        logo = Image.open(BytesIO(logo_response.content)).convert("RGBA")
        logo = logo.resize((100, 100))  # Adjust size as needed

        # Paste the logo onto the image (top-left corner)
        img.paste(logo, (20, 20), logo)

        # Add text
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()  # Default font (can be changed)
        text_position = (50, img.height - 50)  # Position at bottom-left
        draw.text(text_position, text, (255, 255, 255), font=font)

        # Save edited image to memory
        output = BytesIO()
        img.save(output, format="JPEG")
        output.seek(0)

        return send_file(output, mimetype='image/jpeg')

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=10000)
