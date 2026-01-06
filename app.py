import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import textwrap
import random
import io
import os
import glob
import json
import hashlib

# ==========================================
# 🔐 AUTHENTICATION SYSTEM
# ==========================================

USER_DB_FILE = "users.json"


def load_users():
    if not os.path.exists(USER_DB_FILE):
        return {}
    try:
        with open(USER_DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_users(users):
    with open(USER_DB_FILE, "w") as f:
        json.dump(users, f)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(username, password):
    users = load_users()
    if username in users:
        return False, "Username already exists. Please choose another."

    users[username] = hash_password(password)
    save_users(users)
    return True, "Registration successful! You can now login."


def authenticate_user(username, password):
    users = load_users()
    if username not in users:
        return False

    if users[username] == hash_password(password):
        return True
    return False


# ==========================================
# 📝 HANDWRITING ENGINE (The Core Logic)
# ==========================================

def create_realistic_paper(width=1200, height=2200, line_spacing=60):
    paper_color = (248, 247, 240)
    image = Image.new("RGB", (width, height), paper_color)
    draw = ImageDraw.Draw(image)

    # Texture Noise
    pixels = image.load()
    for _ in range(500000):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        r, g, b = pixels[x, y]
        noise = random.randint(5, 20)
        pixels[x, y] = (max(0, r - noise), max(0, g - noise), max(0, b - noise))

    # Grid
    margin_top = 180
    margin_left = 140

    # Blue Lines
    for y in range(margin_top, height - 120, line_spacing):
        line_color = (160 + random.randint(-10, 10), 180 + random.randint(-10, 10), 200)
        draw.line([(0, y), (width, y)], fill=line_color, width=2)

    # Red Margin
    draw.line([(margin_left, 0), (margin_left, height)], fill=(255, 100, 100), width=3)

    return image, margin_left, margin_top


def apply_photo_effects(image):
    # Vignette
    overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    width, height = image.size

    for i in range(0, 150, 5):
        alpha = int((150 - i) * 0.3)
        draw_overlay.rectangle([i, i, width - i, height - i], outline=(0, 0, 0, alpha), width=5)

    # Spine Shadow
    shadow_box = Image.new('RGBA', (100, height), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_box)
    for x in range(100):
        alpha = int((100 - x) * 0.5)
        shadow_draw.line([(x, 0), (x, height)], fill=(0, 0, 0, alpha))
    overlay.paste(shadow_box, (0, 0), shadow_box)

    # Composite
    image = image.convert("RGBA")
    image = Image.alpha_composite(image, overlay).convert("RGB")

    # Blur & Contrast
    image = image.filter(ImageFilter.GaussianBlur(radius=0.7))
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.1)

    return image


def process_text_with_color(raw_text, font, writable_width):
    processed_lines = []
    INK_BLUE = (20, 20, 70)
    INK_BLACK = (25, 25, 25)

    avg_char_width = font.getlength("a") * 0.75
    chars_per_line = int(writable_width / avg_char_width)
    wrapper = textwrap.TextWrapper(width=chars_per_line)

    for paragraph in raw_text.split('\n'):
        if paragraph.startswith('*'):
            current_color = INK_BLACK
            clean_text = paragraph[1:].strip()
        else:
            current_color = INK_BLUE
            clean_text = paragraph

        if not clean_text:
            processed_lines.append(("", current_color))
        else:
            wrapped_lines = wrapper.wrap(clean_text)
            for line in wrapped_lines:
                processed_lines.append((line, current_color))

    return processed_lines


def generate_notebook_pages(main_text, margin_text, font_path, font_size=50):
    if not os.path.exists(font_path):
        return [], f"Error: Font file '{font_path}' not found."

    LINE_SPACING = 60

    try:
        font = ImageFont.truetype(font_path, font_size)
        dummy_paper, m_left, m_top = create_realistic_paper(line_spacing=LINE_SPACING)
    except Exception as e:
        return [], f"Error loading font: {e}"

    body_width = dummy_paper.width - m_left - 28
    body_data = process_text_with_color(main_text, font, body_width)

    margin_width = 100
    margin_data = process_text_with_color(margin_text, font, margin_width)

    total_lines = max(len(body_data), len(margin_data))
    INK_BLUE = (20, 20, 70)
    while len(body_data) < total_lines: body_data.append(("", INK_BLUE))
    while len(margin_data) < total_lines: margin_data.append(("", INK_BLUE))

    pages = []
    current_paper, margin_left, margin_top = create_realistic_paper(line_spacing=LINE_SPACING)
    draw = ImageDraw.Draw(current_paper)
    cursor_y = margin_top + LINE_SPACING

    for i in range(total_lines):
        if cursor_y > current_paper.height - 200:
            realistic_page = apply_photo_effects(current_paper)
            pages.append(realistic_page)

            current_paper, margin_left, margin_top = create_realistic_paper(line_spacing=LINE_SPACING)
            draw = ImageDraw.Draw(current_paper)
            cursor_y = margin_top + LINE_SPACING

        b_text, b_color = body_data[i]
        m_text, m_color = margin_data[i]

        cursor_x = margin_left + random.randint(5, 10)
        for char in b_text:
            vertical_offset = random.randint(-2, 2)
            stroke_w = random.choice([0, 1]) if random.random() > 0.9 else 0
            draw.text((cursor_x, cursor_y + vertical_offset - 5), char, font=font, fill=b_color, anchor="ls",
                      stroke_width=stroke_w, stroke_fill=b_color)
            cursor_x += font.getlength(char)

        m_cursor_x = 20
        for char in m_text:
            vertical_offset = random.randint(-2, 2)
            draw.text((m_cursor_x, cursor_y + vertical_offset - 5), char, font=font, fill=m_color, anchor="ls")
            m_cursor_x += font.getlength(char)

        cursor_y += LINE_SPACING

    realistic_page = apply_photo_effects(current_paper)
    pages.append(realistic_page)

    return pages, None


def get_available_fonts():
    fonts = glob.glob("*.ttf") + glob.glob("*.otf")
    if not fonts: return ["handwriting.ttf"]
    return fonts


# ==========================================
# 🖥️ MAIN UI APPLICATION
# ==========================================

st.set_page_config(page_title="Notebook Generator", layout="wide")

# Check Session State for Login
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = None

# --- AUTHENTICATION PAGE ---
if not st.session_state['logged_in']:
    col_center, _ = st.columns([1, 2])  # Simple centering trick

    with col_center:
        st.title("🔐 Welcome")
        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            login_user = st.text_input("Username", key="login_user")
            login_pass = st.text_input("Password", type="password", key="login_pass")
            if st.button("Login"):
                if authenticate_user(login_user, login_pass):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = login_user
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")

        with tab2:
            reg_user = st.text_input("New Username", key="reg_user")
            reg_pass = st.text_input("New Password", type="password", key="reg_pass")
            if st.button("Register"):
                if reg_user and reg_pass:
                    success, msg = register_user(reg_user, reg_pass)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
                else:
                    st.warning("Please fill in both fields")

# --- MAIN APP PAGE (Only shows after login) ---
else:
    # Sidebar
    with st.sidebar:
        st.write(f"👤 **{st.session_state['username']}**")
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.session_state['username'] = None
            st.rerun()

        st.markdown("---")
        st.title("Configuration")

        st.subheader("Style Settings")
        available_fonts = get_available_fonts()
        selected_font = st.selectbox("Handwriting Font", available_fonts)
        font_size = st.slider("Font Size", 30, 80, 45)

        st.markdown("---")
        st.subheader("View Settings")
        zoom_level = st.slider("Preview Width (px)", min_value=300, max_value=1200, value=600, step=50)

    # Main Content
    st.title("Real-Life Notebook Generator")

    col_margin, col_body = st.columns([1, 4])

    with col_margin:
        st.subheader("Left Margin")
        st.caption("Use * for Black Ink")
        margin_input = st.text_area("Dates / Q.No", height=400, value="Q1.\n\n\n*Q2.")

    with col_body:
        st.subheader("Main Content")
        st.caption("Use * for Black Ink")
        body_default = f"Hello {st.session_state['username']}! Welcome back to your notebook.\n\nEverything is set up. Just type your text here and watch it turn into real handwriting.\n\n*Don't forget to logout when you are done!"
        main_input = st.text_area("Body Text", height=400, value=body_default)

    st.divider()

    if main_input:
        st.subheader("Generated Document")

        with st.spinner("Generating pages..."):
            generated_pages, error = generate_notebook_pages(main_input, margin_input, selected_font, font_size)

        if error:
            st.error(error)
        else:
            col_dl, col_space = st.columns([1, 3])
            with col_dl:
                if len(generated_pages) > 0:
                    pdf_buffer = io.BytesIO()
                    generated_pages[0].save(
                        pdf_buffer, "PDF", resolution=100.0, save_all=True, append_images=generated_pages[1:]
                    )
                    pdf_bytes = pdf_buffer.getvalue()

                    st.download_button(
                        label=f"Download PDF ({len(generated_pages)} Pages)",
                        data=pdf_bytes,
                        file_name="notebook_project.pdf",
                        mime="application/pdf",
                        type="primary",
                        use_container_width=True
                    )

            st.markdown("---")
            for idx, page_img in enumerate(generated_pages):
                st.markdown(f"**Page {idx + 1}**")
                st.image(page_img, width=zoom_level)

                buf = io.BytesIO()
                page_img.save(buf, format="JPEG", quality=95)
                byte_im = buf.getvalue()

                st.download_button(
                    label=f"Download Page {idx + 1} as Image",
                    data=byte_im,
                    file_name=f"notebook_page_{idx + 1}.jpg",
                    mime="image/jpeg",
                    key=f"dl_btn_{idx}"
                )
                st.markdown("---")