from flask import Flask, request, send_file, jsonify
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

app = Flask(__name__)

LOGO_URL = "https://i.postimg.cc/pLmxYnmy/image-1.png"
FONT_PATH = "Montserrat-Bold.ttf"

@app.route('/')
def home():
    return "Flask Image Editor is running!"

@app.route('/edit_image', methods=['POST'])
def edit_image():
    try:
        data = request.get_json()
        image_url = data.get("image_url")
        text = data.get("text", "Default Text")

        # Download and load the image
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content)).convert("RGB")
        img = img.resize((1080, 1080), Image.LANCZOS)

        # Download and resize the logo
        logo_response = requests.get(LOGO_URL)
        logo = Image.open(BytesIO(logo_response.content)).convert("RGBA")
        logo = logo.resize((252, 44), Image.LANCZOS)

        # Create a gradient overlay (black fading upwards)
        gradient = Image.new('L', (img.width, 300), 0)  # 300px high black gradient
        for y in range(gradient.height):
            opacity = int(255 * (y / gradient.height))  # Fade effect
            gradient.putpixel((0, y), opacity)

        # Expand gradient to match width
        gradient = gradient.resize((img.width, gradient.height))
        gradient_overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        gradient_overlay.paste(Image.new("RGBA", (img.width, gradient.height), (0, 0, 0, 255)), (0, img.height - gradient.height), gradient)

        # Merge the gradient with the image
        img = Image.alpha_composite(img.convert("RGBA"), gradient_overlay)

        # Calculate logo position (Centered, 50px from bottom)
        logo_x = (img.width - logo.width) // 2
        logo_y = img.height - logo.height - 50
        img.paste(logo, (logo_x, logo_y), logo)

        # Load font
        font = ImageFont.truetype(FONT_PATH, 56)

        # Add text (Centered, 42px above logo)
        draw = ImageDraw.Draw(img)
        text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:]
        text_x = (img.width - text_width) // 2
        text_y = logo_y - text_height - 42

        # Draw text in white
        draw.text((text_x, text_y), text, (255, 255, 255), font=font)

        # Save edited image to memory
        output = BytesIO()
        img.convert("RGB").save(output, format="JPEG")
        output.seek(0)

        return send_file(output, mimetype='image/jpeg')

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=10000)
