import openai
import requests
from fpdf import FPDF
from io import BytesIO
from PIL import Image
from datetime import datetime
import re

# Setup your OpenAI API key
openai_api_key = "your-api-key-here"

# ==== Generate SEO Title ====
def generate_title():
    client = openai.OpenAI(api_key=openai_api_key)
    response = client.chat.completions.create(
        model="gpt-4",
        messages = [
            {"role": "system", "content": "You are an expert SEO content strategist."},
            {"role": "user", "content": (
                "Generate an SEO-optimized blog post title for a Shopify-focused agency website (borntechies.com). "
                "The company provides Shopify design, development, migration, performance optimization, and ongoing support services. "
                "The target audience is eCommerce business owners, entrepreneurs, and marketers looking to scale their Shopify stores. "
                "The blog title should focus on trending topics related to Shopify, conversion rate optimization, eCommerce design, or AI tools for Shopify. "
                "Make the title helpful, keyword-rich, and click-worthy, as it will be used in a blog post to boost search rankings."
            )}
        ]
    )
    return response.choices[0].message.content.strip()

# ==== Generate Blog Content ====
def generate_blog_content(title):
    client = openai.OpenAI(api_key=openai_api_key)
    prompt = (
        f"Write a 1000-word, SEO-optimized blog post titled '{title}' for borntechies.com — a Shopify development agency. "
        "Structure the content with an engaging introduction, 3-4 informative subheadings, bullet points where useful, and a strong conclusion. "
        "Make it helpful for tech entrepreneurs, marketers, or eCommerce business owners. "
        "Focus on Shopify development, AI tools for eCommerce, automation, SEO strategies for Shopify stores, or web performance optimization. "
        "Use a professional but approachable tone suitable for a tech-savvy audience looking to scale their business."
    )
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a senior content writer."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

# ==== Generate Image ====
def generate_image(prompt):
    client = openai.OpenAI(api_key=openai_api_key)
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        n=1,
        size="1024x1024"
    )
    image_url = response.data[0].url
    image_data = requests.get(image_url).content
    return Image.open(BytesIO(image_data))

# ==== Create PDF ====
class UnicodePDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font("DejaVu", "", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
        self.add_font("DejaVu", "B", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
        self.set_font("DejaVu", size=12)

def create_pdf(title, content, image):
    pdf = UnicodePDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("DejaVu", "B", 16)
    pdf.multi_cell(0, 10, title)
    pdf.ln(5)

    # Save image with unique filename
    today = datetime.now().strftime("%Y-%m-%d")
    safe_title = re.sub(r'\W+', '-', title.lower())[:50]
    image_path = f"{safe_title}_SEO_Image_{today}.jpg"
    image.save(image_path)

    # Insert image in PDF
    pdf.image(image_path, x=10, w=pdf.w - 20)
    pdf.ln(105)

    # Content
    pdf.set_font("DejaVu", "", 12)
    pdf.multi_cell(0, 10, content)

    # Save PDF
    safe_title = re.sub(r'\W+', '-', title.lower())[:50]
    filename = f"{safe_title}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
    pdf.output(filename)
    return filename

# ==== Main Workflow ====
if __name__ == "__main__":
    print("📝 Generating SEO Blog Title...")
    blog_title = generate_title()
    print("✔ Title:", blog_title)

    print("✍️ Generating Blog Content...")
    blog_content = generate_blog_content(blog_title)
    print("✔ Content ready.")

    print("🖼️ Generating AI Image...")
    blog_image = generate_image(f"{blog_title}, digital art, SEO, tech, futuristic")
    print("✔ Image ready.")

    print("📄 Creating PDF...")
    pdf_path = create_pdf(blog_title, blog_content, blog_image)
    print(f"🎉 Blog PDF saved as: {pdf_path}")
