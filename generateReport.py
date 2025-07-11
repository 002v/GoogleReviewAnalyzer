import re
import markdown
from pathlib import Path

def generate_html_report(
    image_path: str,
    markdown_text: str,
    output_html_file: str = "report.html",
    image_width: int = 600
):
    """
    Generates an HTML report with an image followed by Markdown-rendered text.
    Removes known ad blocks from the markdown automatically.

    Args:
        image_path (str): Path to the image file to include.
        markdown_text (str): The raw markdown text to render.
        output_html_file (str): The output path for the HTML file.
        image_width (int): Width of the displayed image in pixels.
    """

    def remove_pollinations_ad(md_text: str) -> str:
        pattern = r"(?m)^---\n\n\*\*Support Pollinations\.AI:\*\*\n.*?pollinations\.ai.*"
        return re.sub(pattern, '', md_text, flags=re.DOTALL).strip()

    # Clean markdown from ad content
    cleaned_md = remove_pollinations_ad(markdown_text)

    # Convert Markdown to HTML
    md_html = markdown.markdown(cleaned_md, extensions=['fenced_code', 'tables'])

    # HTML content structure
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Markdown Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
            }}
            img {{
                width: {image_width}px;
                height: auto;
                display: block;
                margin-bottom: 20px;
                border: 1px solid #ccc;
                border-radius: 10px;
            }}
            pre {{
                background-color: #f4f4f4;
                padding: 20px;
                border-radius: 8px;
                white-space: pre-wrap;
                word-wrap: break-word;
            }}
        </style>
    </head>
    <body>
        <img src="{image_path}" alt="Generated Image">
        <pre>{md_html}</pre>
    </body>
    </html>
    """

    # Save to file
    Path(output_html_file).write_text(html_content, encoding="utf-8")
    print(f"✅ HTML report saved to: {output_html_file}")
