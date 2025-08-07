# AI Blog Generator

This Python script uses OpenAI's GPT-4 and DALL·E to automatically generate an SEO-optimized blog post, create a featured image, and export everything as a nicely formatted PDF.

## Features

- 🔍 **SEO Blog Title Generation**
- ✍️ **1000-word Blog Post Creation**
- 🖼️ **AI-Generated Image (DALL·E 3)**
- 📄 **PDF Export with Title, Image, and Content**

## Requirements

- Python 3.7+
- OpenAI Python SDK
- `requests`, `fpdf`, `Pillow`

## Setup

1. Install dependencies:

```bash
pip install openai requests fpdf pillow
```

2. Set your OpenAI API key in the script:

```python
openai_api_key = "your-api-key-here"
```

3. Run the script:

```bash
python generate_blog.py
```

## Output

- A blog PDF with:
  - SEO title
  - AI-generated image
  - Full-length blog post

## File Structure

- `generate_blog.py` – Main script
- Output PDFs and images are saved in the script directory

