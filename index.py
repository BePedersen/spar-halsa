import os
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape_spar_offers():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://spar.no", wait_until="load")

        try:
            page.wait_for_selector(".product__carousel-container-visible .product", timeout=15000)
        except Exception as e:
            print(f"⚠️ Selector not found or timed out: {e}")
            page.screenshot(path="error_screenshot.png")
            with open("debug.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            browser.close()
            return []

        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")
    offers = []

    products = soup.select(".product__carousel-container-visible .product")

    for p in products:
        title = p.select_one(".product__text--header")
        description = p.select_one(".product__text--sub-text")
        image = p.select_one(".product__image img")

        price_main = p.select_one(".product__price:not(.product__price--sup)")
        price_sup = p.select_one(".product__price--sup")

        if price_main and price_sup:
            price = f"{price_main.get_text(strip=True)},{price_sup.get_text(strip=True)}"
        else:
            price = (price_main or price_sup or "").get_text(strip=True)

        offers.append({
            "title": title.get_text(strip=True) if title else "",
            "description": description.get_text(strip=True) if description else "",
            "price": price,
            "image": image["src"] if image and image.has_attr("src") else ""
        })

    print(f"📦 Found {len(offers)} offers.")
    return offers

def generate_html(offers, image_folder="bilder", video_file="video.mp4"):
    image_tags = ""
    if os.path.exists(image_folder):
        for img_file in os.listdir(image_folder):
            if img_file.lower().endswith(".jpg"):
                image_tags += f'<img class="gallery-image" src="{image_folder}/{img_file}" alt="{img_file}" style="display: none;">\n'

    video_tag = f'<video src="{video_file}" autoplay muted loop></video>' if os.path.exists(video_file) else ""

    html = f"""<!DOCTYPE html>
<html lang="no">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="300">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>SPAR-Visning</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html, body {{
            width: 100%;
            height: 100%;
            overflow: hidden;
            font-family: 'Helvetica Neue', sans-serif;
        }}
        .section {{
            width: 100%;
            height: 100vh;
            position: absolute;
            top: 0;
            left: 0;
            transition: opacity 1s ease-in-out;
            opacity: 0;
            pointer-events: none;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }}
        .active {{
            opacity: 1;
            pointer-events: auto;
            z-index: 1;
        }}
        .carousel-container {{
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .carousel-track {{
            display: flex;
            transition: transform 0.5s ease-in-out;
            width: 100%;
            height: 100%;
        }}
        .slide {{
            display: flex;
            justify-content: center;
            align-items: center;
            flex: 0 0 100%;
            height: 100%;
            gap: 4vw;
            padding: 0 5vw;
        }}
        .offer {{
            width: 40%;
            height: 85%;
            background: #ffffff;
            border-radius: 20px;
            text-align: center;
            box-shadow: 0 6px 15px rgba(0,0,0,0.15);
            padding: 20px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}
        .offer img {{
            max-height: 55vh;
            object-fit: contain;
            border-radius: 15px;
        }}
        .offer h2 {{
            font-size: 4em;
            margin: 10px 0 5px 0;
            color: #333;
        }}
        .offer p {{
            font-size: 1.8em;
            color: #666;
            margin: 0;
        }}
        .offer strong {{
            font-size: 8em;
            color: #d00000;
            margin-top: 10px;
        }}
        .video-section video {{
            width: 100%;
            height: 100vh;
            object-fit: cover;
        }}
        .gallery-section {{
            background: #f5f5f5;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }}
        .gallery img {{
            display: none;
            max-height: 80vh;
            margin: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{
            position: absolute;
            top: 20px;
            width: 100%;
            text-align: center;
            color: #d00000;
            font-size: 3em;
        }}
    </style>
</head>
<body>

<div class="section active" id="section1">
    <h1>Ukens tilbud</h1>
    <div class="carousel-container">
        <div class="carousel-track" id="carouselTrack">
"""

    for i in range(0, len(offers), 2):
        html += '<div class="slide">\n'
        for j in range(2):
            if i + j < len(offers):
                offer = offers[i + j]
                html += f"""
                <div class="offer">
                    <img src="{offer['image']}" alt="{offer['title']}">
                    <h2>{offer['title']}</h2>
                    <p>{offer['description']}</p>
                    <strong>{offer['price']}</strong>
                </div>
                """
        html += '</div>\n'

    html += f"""
        </div>
    </div>
</div>

<div class="section video-section" id="section2">
    {video_tag}
</div>

<div class="section gallery-section" id="section3">
    <div class="gallery">
        {image_tags}
    </div>
</div>

<script>
window.onload = function () {{
    const track = document.getElementById('carouselTrack');
    const slides = document.querySelectorAll('.slide');
    let slideIndex = 0;

    setInterval(() => {{
        slideIndex = (slideIndex + 1) % slides.length;
        track.style.transform = `translateX(-${{slideIndex * 100}}%)`;
    }}, 4000);

    const s1 = document.getElementById('section1');
    const s2 = document.getElementById('section2');
    const s3 = document.getElementById('section3');
    const rotationOrder = [s1, s3, s2, s3];
    let sectionIndex = 0;

    const galleryImages = document.querySelectorAll('.gallery-image');

    function showRandomGalleryImage() {{
        galleryImages.forEach(img => img.style.display = 'none');
        const rand = Math.floor(Math.random() * galleryImages.length);
        galleryImages[rand].style.display = 'block';
    }}

    setInterval(() => {{
        [s1, s2, s3].forEach(s => s.classList.remove('active'));
        const currentSection = rotationOrder[sectionIndex];
        currentSection.classList.add('active');

        if (currentSection === s3 && galleryImages.length > 0) {{
            showRandomGalleryImage();
        }}

        sectionIndex = (sectionIndex + 1) % rotationOrder.length;
    }}, 8000);
}}
</script>

</body>
</html>
"""
    return html

if __name__ == "__main__":
    offers = scrape_spar_offers()
    html = generate_html(offers)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ HTML-side generert: index.html")