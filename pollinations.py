import requests
import base64

url = "https://text.pollinations.ai/openai"
headers = {"Content-Type": "application/json"}

# Helper function to encode local image to base64
def encode_image_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"Error: Image file not found at {image_path}")
        return None

def analyze_local_image(image_path, question="As an expert in analysing graphs,in a step by step process explain the attached graph which consist of 4 main parts and at the end of the conclusion suggest from 10 if that place is worth going to for example 5/10 or 8/10 "):
    base64_image = encode_image_base64(image_path)
    if not base64_image:
        return None

    # Determine image format (simple check by extension)
    image_format = image_path.split('.')[-1].lower()
    if image_format not in ['jpeg', 'jpg', 'png']:
         print(f"Warning: Potentially unsupported image format '{image_format}'. Assuming jpeg.")
         image_format = 'jpeg' # Default or make more robust for unknown formats

    payload = {
        "model": "openai", # Ensure this model supports vision
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {
                        "type": "image_url",
                        "image_url": {
                           "url": f"data:image/{image_format};base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 500
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error analyzing local image: {e}")
        # if response is not None: print(response.text) # Show error from API
        return None


