"""
Simple test of ImageOCRReader without LlamaIndex integration
"""

import os
from ocr_research.image_ocr_reader import ImageOCRReader
from PIL import Image, ImageDraw, ImageFont

def create_test_image():
    """Create a simple test image with Chinese text"""

    images_dir = os.path.join(os.path.dirname(__file__), "test_images")
    os.makedirs(images_dir, exist_ok=True)

    # Create a simple image with text
    img = Image.new('RGB', (800, 400), color='white')
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/System/Library/Fonts/STHeiti Light.ttc", 40)
    except:
        font = ImageFont.load_default()

    # Draw text
    draw.text((50, 50), "人工智能技术", fill='black', font=font)
    draw.text((50, 150), "创建日期：2025年3月20日", fill='black', font=font)
    draw.text((50, 250), "版本：v1.0", fill='black', font=font)

    img_path = os.path.join(images_dir, "test_simple.png")
    img.save(img_path)

    print(f"Created test image: {img_path}")
    return img_path

def main():
    print("="*60)
    print("Basic OCR Test")
    print("="*60)

    # Create test image
    img_path = create_test_image()

    # Initialize OCR reader
    print("\nInitializing PaddleOCR...")
    reader = ImageOCRReader(lang='ch', use_gpu=False, show_log=False)

    # Test OCR
    print(f"\nProcessing image: {img_path}")
    documents = reader.load_data(img_path)

    if documents:
        doc = documents[0]
        print("\n" + "="*60)
        print("OCR Results")
        print("="*60)
        print(f"Image: {doc.metadata['file_name']}")
        print(f"Text blocks detected: {doc.metadata['num_text_blocks']}")
        print(f"Average confidence: {doc.metadata['avg_confidence']:.4f}")
        print(f"\nExtracted text:")
        print(doc.text)
        print("\n" + "="*60)
        print("Success!")
    else:
        print("No text detected")

if __name__ == "__main__":
    main()
