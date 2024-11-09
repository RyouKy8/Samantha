import os
import base64

from together import Together

client = Together(api_key=os.environ.get("TOGETHER_API_KEY"))

# Generate image using the Together API
response = client.images.generate(
    prompt="A beautiful sunset over a mountain range",
    model="black-forest-labs/FLUX.1-schnell-Free",
    width=1024,
    height=768,
    steps=4,
    n=1,
    response_format="b64_json",
)

# Get the base64-encoded image from the response
b64_image = response.data[0].b64_json

# Decode the base64 string to binary data
image_data = base64.b64decode(b64_image)

# Save the image to your local system as a .png file
with open("generated_image.png", "wb") as f:
    f.write(image_data)

print("Image saved as 'generated_image.png'")
