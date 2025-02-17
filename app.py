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

        # 1. Download and load the base image
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content)).convert("RGB")
        img = img.resize((1080, 1080), Image.LANCZOS)

        # 2. Download and resize the logo
        logo_response = requests.get(LOGO_URL)
        logo = Image.open(BytesIO(logo_response.content)).convert("RGBA")
        logo = logo.resize((252, 44), Image.LANCZOS)

        # 3. Create a smooth black gradient at the bottom
        gradient_height = 300
        gradient = Image.new('L', (img.width, gradient_height), 0)
        for y in range(gradient.height):
            # fade from transparent (0) at top to opaque (255) at bottom
            opacity = int(255 * (y / float(gradient.height)))
            gradient.putpixel((0, y), opacity)

        gradient = gradient.resize((img.width, gradient_height))
        gradient_overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        # Paste a solid black rectangle, masked by our gradient
        gradient_overlay.paste(
            Image.new("RGBA", (img.width, gradient_height), (0, 0, 0, 255)),
            (0, img.height - gradient_height),
            gradient
        )
        img = Image.alpha_composite(img.convert("RGBA"), gradient_overlay)

        # 4. Paste the logo (centered, 50px from bottom)
        logo_x = (img.width - logo.width) // 2
        logo_y = img.height - logo.height - 50
        img.paste(logo, (logo_x, logo_y), logo)

        # 5. Prepare to draw text
        draw = ImageDraw.Draw(img)
        font_size = 56
        font = ImageFont.truetype(FONT_PATH, font_size)

        # 6. Wrap text so it doesn't go beyond image width (with some padding)
        max_text_width = int(img.width * 0.85)  # 85% of width for safety
        lines = wrap_text(draw, text, font, max_text_width)
        line_height = draw.textbbox((0, 0), "Ay", font=font)[3]  # approximate line height
        num_lines = len(lines)

        # 7. Calculate total text height
        total_text_height = line_height * num_lines

        # We want the **bottom line** to be 42px above the logo
        bottom_line_y = logo_y - 42 - line_height  # This is where the last line starts
        # So the top line will be:
        top_line_y = bottom_line_y - (num_lines - 1) * line_height

        # 8. Draw a semi-transparent black rectangle behind the wrapped text
        #    This ensures high contrast even if the gradient isn't dark enough
        text_overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(text_overlay)

        # Rectangle bounds
        padding = 20
        rect_left = 0
        rect_top = top_line_y - padding
        rect_right = img.width
        rect_bottom = bottom_line_y + line_height + padding

        # Make sure we don't go above the image if text is large
        if rect_top < 0:
            rect_top = 0

        overlay_draw.rectangle(
            [rect_left, rect_top, rect_right, rect_bottom],
            fill=(0, 0, 0, 180)  # black with ~70% opacity
        )

        # 9. Draw each line centered horizontally
        current_y = top_line_y
        for line in lines:
            text_width, text_height = draw.textbbox((0, 0), line, font=font)[2:]
            text_x = (img.width - text_width) // 2
            overlay_draw.text((text_x, current_y), line, font=font, fill=(255, 255, 255, 255))
            current_y += line_height

        # 10. Composite the text overlay onto the original image
        img = Image.alpha_composite(img, text_overlay)

        # 11. Output final image
        output = BytesIO()
        img.convert("RGB").save(output, format="JPEG", quality=90)
        output.seek(0)

        return send_file(output, mimetype='image/jpeg')

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=10000)
