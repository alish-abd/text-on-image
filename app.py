from flask import Flask, request, send_file, jsonify
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

app = Flask(__name__)

# Logo URL (Replace with your actual logo URL)
LOGO_URL = "https://i.postimg.cc/pLmxYnmy/image-1.png"

# Load font from local file
FONT_PATH = "Montserrat-Bold.ttf"

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
        img = Image.open(BytesIO(response.content)).convert("RGB")

        # Resize image to 1080x1080 while maintaining aspect ratio
        img = img.resize((1080, 1080), Image.LANCZOS)

        # Download and resize the logo (252x44)
        logo_response = requests.get(LOGO_URL)
        logo = Image.open(BytesIO(logo_response.content)).convert("RGBA")
        logo = logo.resize((252, 44), Image.LANCZOS)

        # Calculate position for the logo (Centered, 50px from bottom)
        logo_x = (img.width - logo.width) // 2
        logo_y = img.height - logo.height - 50

        # Paste the logo onto the image
        img.paste(logo, (logo_x, logo_y), logo)

        # Load Montserrat font (Size 56px)
        font = ImageFont.truetype(FONT_PATH, 56)

        # Add text (Centered, 42px above logo)
        draw = ImageDraw.Draw(img)
        text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:]
        text_x = (img.width - text_width) // 2
        text_y = logo_y - text_height - 42  # 42px above logo

        # Draw text in white
        draw.text((text_x, text_y), text, (255, 255, 255), font=font)

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
