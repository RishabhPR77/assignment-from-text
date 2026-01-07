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
# 🔐 AUTHENTICATION & SETUP
# ==========================================
USER_DB_FILE = "users.json"


def load_users():
    if not os.path.exists(USER_DB_FILE): return {}
    try:
        with open(USER_DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_users(users):
    with open(USER_DB_FILE, "w") as f: json.dump(users, f)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(username, password):
    users = load_users()
    if username in users: return False, "Username exists."
    users[username] = hash_password(password)
    save_users(users)
    return True, "Registered."


def authenticate_user(username, password):
    users = load_users()
    if username not in users: return False
    if users[username] == hash_password(password): return True
    return False


# ==========================================
# 📝 HANDWRITING ENGINE
# ==========================================

def create_realistic_paper(width=1200, height=2200, line_spacing=60):
    paper_color = (248, 247, 240)
    image = Image.new("RGB", (width, height), paper_color)
    draw = ImageDraw.Draw(image)

    # Noise
    pixels = image.load()
    for _ in range(500000):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        r, g, b = pixels[x, y]
        noise = random.randint(5, 20)
        pixels[x, y] = (max(0, r - noise), max(0, g - noise), max(0, b - noise))

    # Lines
    margin_top = 180
    margin_left = 140

    for y in range(margin_top, height - 120, line_spacing):
        line_color = (160 + random.randint(-10, 10), 180 + random.randint(-10, 10), 200)
        draw.line([(0, y), (width, y)], fill=line_color, width=2)

    draw.line([(margin_left, 0), (margin_left, height)], fill=(255, 100, 100), width=3)
    return image, margin_left, margin_top


def apply_photo_effects(image):
    overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    width, height = image.size
    for i in range(0, 150, 5):
        alpha = int((150 - i) * 0.3)
        draw_overlay.rectangle([i, i, width - i, height - i], outline=(0, 0, 0, alpha), width=5)

    shadow_box = Image.new('RGBA', (100, height), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_box)
    for x in range(100):
        alpha = int((100 - x) * 0.5)
        shadow_draw.line([(x, 0), (x, height)], fill=(0, 0, 0, alpha))
    overlay.paste(shadow_box, (0, 0), shadow_box)

    image = image.convert("RGBA")
    image = Image.alpha_composite(image, overlay).convert("RGB")
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
            for line in wrapped_lines: processed_lines.append((line, current_color))
    return processed_lines


# --- HEADER ENGINE ---
def draw_header(draw, font_path, header_size, header_data, margin_left):
    if not header_data or not header_data.get("enabled", False):
        return 160

    INK_BLACK = (25, 25, 25)
    INK_BLUE = (20, 20, 70)
    header_font = ImageFont.truetype(font_path, header_size)

    start_x = margin_left + header_data.get("x_offset", 20)
    current_y = header_data.get("y_offset", 20)

    line_height = int(header_size * 1.1)

    def draw_line(label, value, y):
        if value:
            draw.text((start_x, y), label, font=header_font, fill=INK_BLACK)
            label_w = header_font.getlength(label)
            draw.text((start_x + label_w, y), value, font=header_font, fill=INK_BLUE)
            return line_height
        return 0

    current_y += draw_line("Name: ", header_data.get("name"), current_y)
    current_y += draw_line("Enrollment No: ", header_data.get("enrollment"), current_y)
    current_y += draw_line("Subject: ", header_data.get("subject"), current_y)

    return current_y + 10


# --- PAGE GENERATOR ---
def generate_notebook_pages(main_text, margin_text, font_path, body_font_size, page_headers_map, header_font_size):
    if not os.path.exists(font_path): return [], f"Missing font: {font_path}"

    LINE_SPACING = 60
    try:
        font = ImageFont.truetype(font_path, body_font_size)
        dummy_paper, m_left, m_top = create_realistic_paper(line_spacing=LINE_SPACING)
    except Exception as e:
        return [], f"Font Error: {e}"

    body_width = dummy_paper.width - m_left - 28
    body_data = process_text_with_color(main_text, font, body_width)
    margin_width = 100
    margin_data = process_text_with_color(margin_text, font, margin_width)

    total_lines = max(len(body_data), len(margin_data))
    INK_BLUE = (20, 20, 70)
    while len(body_data) < total_lines: body_data.append(("", INK_BLUE))
    while len(margin_data) < total_lines: margin_data.append(("", INK_BLUE))

    pages = []

    # Page 1 Init
    current_paper, margin_left, margin_top = create_realistic_paper(line_spacing=LINE_SPACING)
    draw = ImageDraw.Draw(current_paper)

    # Check header for Page 0
    header_end_y = draw_header(draw, font_path, header_font_size, page_headers_map.get(0), margin_left)

    start_y_body = max(margin_top + 20, header_end_y)
    cursor_y = margin_top + LINE_SPACING
    while cursor_y < start_y_body:
        cursor_y += LINE_SPACING

    current_page_idx = 0

    for i in range(total_lines):
        if cursor_y > current_paper.height - 200:
            realistic_page = apply_photo_effects(current_paper)
            pages.append(realistic_page)

            # New Page
            current_page_idx += 1
            current_paper, margin_left, margin_top = create_realistic_paper(line_spacing=LINE_SPACING)
            draw = ImageDraw.Draw(current_paper)

            # Check header for this new page index
            header_end_y = draw_header(draw, font_path, header_font_size, page_headers_map.get(current_page_idx),
                                       margin_left)

            start_y_body = max(margin_top + 20, header_end_y)
            cursor_y = margin_top + LINE_SPACING
            while cursor_y < start_y_body:
                cursor_y += LINE_SPACING

        b_text, b_color = body_data[i]
        m_text, m_color = margin_data[i]

        cursor_x = margin_left + random.randint(5, 10)
        for char in b_text:
            v_off = random.randint(-2, 2)
            s_w = random.choice([0, 1]) if random.random() > 0.9 else 0
            draw.text((cursor_x, cursor_y + v_off - 5), char, font=font, fill=b_color, anchor="ls", stroke_width=s_w,
                      stroke_fill=b_color)
            cursor_x += font.getlength(char)

        m_x = 20
        for char in m_text:
            v_off = random.randint(-2, 2)
            draw.text((m_x, cursor_y + v_off - 5), char, font=font, fill=m_color, anchor="ls")
            m_x += font.getlength(char)

        cursor_y += LINE_SPACING

    realistic_page = apply_photo_effects(current_paper)
    pages.append(realistic_page)
    return pages, None


def get_available_fonts():
    fonts = glob.glob("*.ttf") + glob.glob("*.otf")
    if not fonts: return ["handwriting.ttf"]
    return fonts


# ==========================================
# 🖥️ UI
# ==========================================
st.set_page_config(page_title="Notebook Generator", layout="wide")

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'username' not in st.session_state: st.session_state['username'] = None
if 'page_headers' not in st.session_state: st.session_state['page_headers'] = {}

# LOGIN
if not st.session_state['logged_in']:
    col_center, _ = st.columns([1, 2])
    with col_center:
        st.title("Welcome")
        tab1, tab2 = st.tabs(["Login", "Register"])
        with tab1:
            u = st.text_input("User", key="u")
            p = st.text_input("Pass", type="password", key="p")
            if st.button("Login"):
                if authenticate_user(u, p):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = u
                    # Default Page 1 Header
                    st.session_state['page_headers'][0] = {
                        "enabled": True, "name": u, "enrollment": "123456", "subject": "Subject", "x_offset": 20,
                        "y_offset": 20
                    }
                    st.rerun()
                else:
                    st.error("Invalid")
        with tab2:
            ru = st.text_input("New User", key="ru")
            rp = st.text_input("New Pass", type="password", key="rp")
            if st.button("Register"):
                if ru and rp:
                    s, m = register_user(ru, rp)
                    if s:
                        st.success(m)
                    else:
                        st.error(m)
else:
    # APP
    with st.sidebar:
        st.write(f"User: **{st.session_state['username']}**")
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.session_state['page_headers'] = {}
            st.rerun()
        st.markdown("---")
        st.title("Settings")
        sel_font = st.selectbox("Font", get_available_fonts())
        body_fs = st.slider("Body Font Size", 30, 80, 45)
        zoom = st.slider("Zoom", 300, 1200, 600, 50)

    st.title("Real-Life Notebook Generator")

    c1, c2 = st.columns([1, 4])
    with c1:
        st.subheader("Margin")
        m_in = st.text_area("Dates / Q.No", height=300, value="Q1.\n\n\n*Q2.")
    with c2:
        st.subheader("Body")
        b_in = st.text_area("Text", height=300,
                            value="Every page now has its own 'Header Panel' on the right side.\n\nYou can independently control the name, subject, and position for Page 1, Page 2, etc.")

    st.divider()

    # GENERATE
    if b_in:
        with st.spinner("Generating..."):
            pages, err = generate_notebook_pages(b_in, m_in, sel_font, body_fs, st.session_state['page_headers'], 40)

        if err:
            st.error(err)
        else:
            # ALL PDF
            pdf_buf = io.BytesIO()
            if pages:
                pages[0].save(pdf_buf, "PDF", resolution=100.0, save_all=True, append_images=pages[1:])
                st.download_button("Download All (PDF)", pdf_buf.getvalue(), "doc.pdf", "application/pdf",
                                   type="primary")

            st.markdown("---")

            # --- RESULTS LOOP WITH SIDE PANEL ---
            for i, p in enumerate(pages):
                st.markdown(f"### Page {i + 1}")

                # Split: Image (Left) vs Settings (Right)
                col_img, col_settings = st.columns([2, 1])

                # --- LEFT: IMAGE ---
                with col_img:
                    st.image(p, width=zoom)

                    # Image Download
                    img_buf = io.BytesIO()
                    p.save(img_buf, "JPEG", quality=95)
                    st.download_button(f"Download Page {i + 1}", img_buf.getvalue(), f"p{i + 1}.jpg", "image/jpeg",
                                       key=f"dl_{i}", use_container_width=True)

                # --- RIGHT: HEADER PANEL ---
                with col_settings:
                    # Retrieve current data for this page (or default empty)
                    current_header = st.session_state['page_headers'].get(i, {
                        "enabled": False,
                        "name": st.session_state['username'],
                        "enrollment": "",
                        "subject": "",
                        "x_offset": 20,
                        "y_offset": 20
                    })

                    # We use a FORM so the app doesn't reload on every keystroke
                    with st.form(key=f"header_form_{i}"):
                        st.write(f"**Header Settings (Page {i + 1})**")

                        enable_h = st.checkbox("Enable Header", value=current_header["enabled"])

                        h_name = st.text_input("Name", value=current_header["name"])
                        h_enr = st.text_input("Enrollment", value=current_header["enrollment"])
                        h_sub = st.text_input("Subject", value=current_header["subject"])

                        st.markdown("---")
                        st.caption("Position Adjustment")
                        h_x = st.slider("Left-Right", 0, 200, current_header["x_offset"])
                        h_y = st.slider("Up-Down", 0, 300, current_header["y_offset"])

                        # Apply Button
                        if st.form_submit_button("Apply Header Changes", type="primary"):
                            # Update Session State
                            st.session_state['page_headers'][i] = {
                                "enabled": enable_h,
                                "name": h_name,
                                "enrollment": h_enr,
                                "subject": h_sub,
                                "x_offset": h_x,
                                "y_offset": h_y
                            }
                            st.rerun()

                st.divider()