import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
import textwrap
import random
import io
import os
import glob
import json
import hashlib

# ==========================================
# AUTHENTICATION & SETUP
# ==========================================
USER_DB_FILE = "users.json"

def load_users():
    if not os.path.exists(USER_DB_FILE): return {}
    try:
        with open(USER_DB_FILE, "r") as f: return json.load(f)
    except: return {}

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
# HANDWRITING ENGINE
# ==========================================

def create_realistic_paper(width=1200, height=2200, line_spacing=60):
    base_r = 248 + random.randint(-2, 2)
    base_g = 247 + random.randint(-2, 2)
    base_b = 240 + random.randint(-2, 2)
    paper_color = (base_r, base_g, base_b)
    
    image = Image.new("RGB", (width, height), paper_color)
    draw = ImageDraw.Draw(image)

    pixels = image.load()
    for _ in range(400000):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        r, g, b = pixels[x, y]
        noise = random.randint(5, 20)
        pixels[x, y] = (max(0, r - noise), max(0, g - noise), max(0, b - noise))

    margin_top = 180
    margin_left = 140

    for y in range(margin_top, height - 120, line_spacing):
        line_color = (160, 180, 210)
        draw.line([(0, y), (width, y)], fill=line_color, width=2)

    draw.line([(margin_left, 0), (margin_left, height)], fill=(255, 100, 100), width=3)
    return image, margin_left, margin_top

# --- 10 SELECTABLE EFFECTS ---
def apply_specific_effect(image, effect_name):
    width, height = image.size
    overlay = Image.new('RGBA', image.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)

    if effect_name == "Scanner Clean":
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.05)
        return image

    elif effect_name == "Warm Lamp":
        draw.rectangle([0,0,width,height], fill=(255, 200, 100, 40))
        image = image.convert("RGBA")
        image = Image.alpha_composite(image, overlay).convert("RGB")
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.1)

    elif effect_name == "Cool Daylight":
        draw.rectangle([0,0,width,height], fill=(200, 220, 255, 40))
        image = image.convert("RGBA")
        image = Image.alpha_composite(image, overlay).convert("RGB")
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.05)

    elif effect_name == "Shadow Left":
        for x in range(250):
            alpha = int((250 - x) * 0.5)
            draw.line([(x, 0), (x, height)], fill=(0,0,0, alpha))
        image = image.convert("RGBA")
        image = Image.alpha_composite(image, overlay).convert("RGB")

    elif effect_name == "Shadow Right":
        for x in range(250):
            alpha = int((250 - x) * 0.5)
            draw.line([(width-x, 0), (width-x, height)], fill=(0,0,0, alpha))
        image = image.convert("RGBA")
        image = Image.alpha_composite(image, overlay).convert("RGB")

    elif effect_name == "Top Angle":
        for y in range(400):
            alpha = int((400 - y) * 0.4)
            draw.line([(0, y), (width, y)], fill=(0,0,0, alpha))
        image = image.convert("RGBA")
        image = Image.alpha_composite(image, overlay).convert("RGB")

    elif effect_name == "High Contrast":
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.4)
        enhancer_b = ImageEnhance.Brightness(image)
        image = enhancer_b.enhance(1.1)

    elif effect_name == "Low Light":
        draw.rectangle([0,0,width,height], fill=(0, 0, 0, 50))
        image = image.convert("RGBA")
        image = Image.alpha_composite(image, overlay).convert("RGB")
        img_pixels = image.load()
        for _ in range(100000):
             x = random.randint(0, width-1)
             y = random.randint(0, height-1)
             image.putpixel((x,y), (max(0, img_pixels[x,y][0]-30), max(0, img_pixels[x,y][1]-30), max(0, img_pixels[x,y][2]-30)))

    elif effect_name == "B&W Xerox":
        image = ImageOps.grayscale(image).convert("RGB")
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)

    elif effect_name == "Vintage/Old":
        draw.rectangle([0,0,width,height], fill=(112, 66, 20, 60))
        image = image.convert("RGBA")
        image = Image.alpha_composite(image, overlay).convert("RGB")
        image = image.filter(ImageFilter.GaussianBlur(radius=1))

    if effect_name != "Scanner Clean":
        angle = random.uniform(-0.5, 0.5)
        image = image.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=(248, 247, 240))

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
        
        if not clean_text: processed_lines.append(("", current_color))
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
    except Exception as e: return [], f"Font Error: {e}"

    body_width = dummy_paper.width - m_left - 28
    body_data = process_text_with_color(main_text, font, body_width)
    margin_width = 100 
    margin_data = process_text_with_color(margin_text, font, margin_width)

    total_lines = max(len(body_data), len(margin_data))
    INK_BLUE = (20, 20, 70)
    while len(body_data) < total_lines: body_data.append(("", INK_BLUE))
    while len(margin_data) < total_lines: margin_data.append(("", INK_BLUE))

    raw_pages = []
    
    current_paper, margin_left, margin_top = create_realistic_paper(line_spacing=LINE_SPACING)
    draw = ImageDraw.Draw(current_paper)
    
    header_end_y = draw_header(draw, font_path, header_font_size, page_headers_map.get(0), margin_left)
    start_y_body = max(margin_top + 20, header_end_y)
    cursor_y = margin_top + LINE_SPACING
    while cursor_y < start_y_body: cursor_y += LINE_SPACING

    current_page_idx = 0

    for i in range(total_lines):
        if cursor_y > current_paper.height - 200:
            raw_pages.append(current_paper)
            
            current_page_idx += 1
            current_paper, margin_left, margin_top = create_realistic_paper(line_spacing=LINE_SPACING)
            draw = ImageDraw.Draw(current_paper)
            
            header_end_y = draw_header(draw, font_path, header_font_size, page_headers_map.get(current_page_idx), margin_left)
            start_y_body = max(margin_top + 20, header_end_y)
            cursor_y = margin_top + LINE_SPACING
            while cursor_y < start_y_body: cursor_y += LINE_SPACING

        b_text, b_color = body_data[i]
        m_text, m_color = margin_data[i]

        cursor_x = margin_left + random.randint(5, 10)
        for char in b_text:
            v_off = random.randint(-2, 2)
            s_w = random.choice([0, 1]) if random.random() > 0.9 else 0
            draw.text((cursor_x, cursor_y + v_off - 5), char, font=font, fill=b_color, anchor="ls", stroke_width=s_w, stroke_fill=b_color)
            cursor_x += font.getlength(char)

        m_x = 20
        for char in m_text:
            v_off = random.randint(-2, 2)
            draw.text((m_x, cursor_y + v_off - 5), char, font=font, fill=m_color, anchor="ls")
            m_x += font.getlength(char)

        cursor_y += LINE_SPACING

    raw_pages.append(current_paper)

    final_pages = []
    for i, p in enumerate(raw_pages):
        effect_name = page_headers_map.get(i, {}).get("effect", "Warm Lamp")
        final_pages.append(apply_specific_effect(p, effect_name))
        
    return final_pages, None

def get_available_fonts():
    fonts = glob.glob("*.ttf") + glob.glob("*.otf")
    if not fonts: return ["handwriting.ttf"]
    return fonts

# ==========================================
# UI
# ==========================================
st.set_page_config(page_title="Notebook Generator", layout="wide")

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'username' not in st.session_state: st.session_state['username'] = None
if 'page_headers' not in st.session_state: st.session_state['page_headers'] = {}

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
                    st.session_state['page_headers'][0] = {
                        "enabled": True, "name": u, "enrollment": "123456", "subject": "Subject", "x_offset": 20, "y_offset": 20, "effect": "Warm Lamp"
                    }
                    st.rerun()
                else: st.error("Invalid")
        with tab2:
            ru = st.text_input("New User", key="ru")
            rp = st.text_input("New Pass", type="password", key="rp")
            if st.button("Register"):
                if ru and rp:
                    s, m = register_user(ru, rp)
                    if s: st.success(m)
                    else: st.error(m)
else:
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
        b_in = st.text_area("Text", height=300, value="Select a specific 'Photo Effect' for each page from the panel on the right.\n\nOptions include: Warm Lamp, Cool Daylight, Shadows, Xerox, etc.")

    st.divider()

    if b_in:
        with st.spinner("Applying Effects..."):
            pages, err = generate_notebook_pages(b_in, m_in, sel_font, body_fs, st.session_state['page_headers'], 40)
        
        if err: st.error(err)
        else:
            pdf_buf = io.BytesIO()
            if pages:
                pages[0].save(pdf_buf, "PDF", resolution=100.0, save_all=True, append_images=pages[1:])
                st.download_button("Download All (PDF)", pdf_buf.getvalue(), "doc.pdf", "application/pdf", type="primary")

            st.markdown("---")
            
            effect_options = [
                "Warm Lamp", "Scanner Clean", "Cool Daylight", 
                "Shadow Left", "Shadow Right", "Top Angle", 
                "High Contrast", "Low Light", "B&W Xerox", "Vintage/Old"
            ]

            for i, p in enumerate(pages):
                st.markdown(f"### Page {i+1}")
                col_img, col_settings = st.columns([2, 1])
                
                with col_img:
                    st.image(p, width=zoom)
                    img_buf = io.BytesIO()
                    p.save(img_buf, "JPEG", quality=95)
                    st.download_button(f"Download Page {i+1}", img_buf.getvalue(), f"p{i+1}.jpg", "image/jpeg", key=f"dl_{i}", use_container_width=True)

                with col_settings:
                    current_header = st.session_state['page_headers'].get(i, {
                        "enabled": False, "name": st.session_state['username'], "enrollment": "", "subject": "", 
                        "x_offset": 20, "y_offset": 20, "effect": "Warm Lamp"
                    })
                    
                    with st.form(key=f"header_form_{i}"):
                        st.write(f"**Page {i+1} Settings**")
                        
                        st.markdown("##### Photo Effect")
                        selected_effect = st.selectbox("Choose Style", effect_options, index=effect_options.index(current_header.get("effect", "Warm Lamp")))
                        
                        st.markdown("---")
                        st.markdown("##### Header Details")
                        enable_h = st.checkbox("Enable Header", value=current_header["enabled"])
                        h_name = st.text_input("Name", value=current_header["name"])
                        h_enr = st.text_input("Enrollment", value=current_header["enrollment"])
                        h_sub = st.text_input("Subject", value=current_header["subject"])
                        
                        st.caption("Position")
                        h_x = st.slider("Left-Right", 0, 200, current_header["x_offset"])
                        h_y = st.slider("Up-Down", 0, 300, current_header["y_offset"])
                        
                        if st.form_submit_button("Apply Changes", type="primary"):
                            st.session_state['page_headers'][i] = {
                                "enabled": enable_h, "name": h_name, "enrollment": h_enr, "subject": h_sub, 
                                "x_offset": h_x, "y_offset": h_y, 
                                "effect": selected_effect
                            }
                            st.rerun()
                st.divider()