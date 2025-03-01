from flask import Flask, request, send_file, jsonify
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

app = Flask(__name__)

# Default logo URL can still be used if none is provided in the request.
DEFAULT_LOGO_URL = "https://i.postimg.cc/pLmxYnmy/image-1.png"
FONT_PATH = "Montserrat-Bold.ttf"

@app.route('/')
def home():
    return "Flask Image Editor is running!"

def wrap_text(draw, text, font, max_width):
    """
    Splits 'text' into multiple lines so that
    each line does not exceed 'max_width'.
    """
    words = text.split()
    if not words:
        return [""]  # Handle empty text

    lines = []
    current_line = words[0]

    for word in words[1:]:
        test_line = current_line + " " + word
        w, _ = draw.textbbox((0, 0), test_line, font=font)[2:]
        if w <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    lines.append(current_line)  # Add the last line
    return lines

@app.route('/edit_image', methods=['POST'])
def edit_image():
    try:
        data = request.get_json()
        image_url = data.get("image_url")
        text = data.get("text", "Default Text")
        logo_url = data.get("logo_url", DEFAULT_LOGO_URL)

        # 1. Download and load the base image
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content)).convert("RGB")
        img = img.resize((1080, 1080), Image.LANCZOS)

        # 2. Download and resize the logo using the provided logo_url
        logo_response = requests.get(logo_url)
        logo = Image.open(BytesIO(logo_response.content)).convert("RGBA")
        logo = logo.resize((252, 44), Image.LANCZOS)

        # 3. Create a vertical gradient from bottom (80% black) to midpoint (0% black)
        half_height = img.height // 2  # The gradient will cover the bottom half
        # Single-column gradient (1 px wide, half_height tall)
        gradient_col = Image.new('L', (1, half_height), 0)
        
        # Fill from top (0% alpha) to bottom (80% alpha = ~204)
        for y in range(half_height):
            alpha = int(204 * (y / float(half_height - 1)))
            gradient_col.putpixel((0, y), alpha)

        # Stretch that single-column gradient to the full image width
        gradient = gradient_col.resize((img.width, half_height))

        # 4. Paste the black rectangle masked by our gradient onto the bottom half
        gradient_overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        black_rect = Image.new("RGBA", (img.width, half_height), (0, 0, 0, 255))
        gradient_overlay.paste(black_rect, (0, img.height - half_height), gradient)

        # 5. Merge the gradient overlay with the image
        img = Image.alpha_composite(img.convert("RGBA"), gradient_overlay)

        # 6. Paste the logo (centered, 50px from bottom)
        logo_x = (img.width - logo.width) // 2
        logo_y = img.height - logo.height - 50
        img.paste(logo, (logo_x, logo_y), logo)

        # 7. Prepare to draw text (wrap to avoid overflow)
        draw = ImageDraw.Draw(img)
        font_size = 56
        font = ImageFont.truetype(FONT_PATH, font_size)

        max_text_width = int(img.width * 0.85)  # 85% of width
        lines = wrap_text(draw, text, font, max_text_width)
        line_height = draw.textbbox((0, 0), "Ay", font=font)[3]  # approximate line height
        num_lines = len(lines)

        # 8. Calculate total text height & position
        total_text_height = line_height * num_lines
        bottom_line_y = logo_y - 42 - line_height  # Bottom line is 42px above the logo
        top_line_y = bottom_line_y - (num_lines - 1) * line_height

        # 9. Draw each line centered horizontally
        current_y = top_line_y
        for line in lines:
            text_width, _ = draw.textbbox((0, 0), line, font=font)[2:]
            text_x = (img.width - text_width) // 2
            draw.text((text_x, current_y), line, font=font, fill=(255, 255, 255, 255))
            current_y += line_height

        # 10. Output final image
        output = BytesIO()
        img.convert("RGB").save(output, format="JPEG", quality=90)
        output.seek(0)

        return send_file(output, mimetype='image/jpeg')

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=10000)
