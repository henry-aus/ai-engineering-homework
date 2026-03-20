"""
OCR Image Text Loader - Main Testing and Integration
"""

import os
from dotenv import load_dotenv
from llama_index.core import Settings, VectorStoreIndex
from llama_index.llms.openai_like import OpenAILike
from llama_index.embeddings.dashscope import DashScopeEmbedding, DashScopeTextEmbeddingModels
from ocr_research.image_ocr_reader import ImageOCRReader
from PIL import Image, ImageDraw, ImageFont
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure LlamaIndex
Settings.llm = OpenAILike(
    model="qwen-plus",
    api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    is_chat_model=True
)

Settings.embed_model = DashScopeEmbedding(
    model_name=DashScopeTextEmbeddingModels.TEXT_EMBEDDING_V3,
    embed_batch_size=6,
    embed_input_length=8192
)


def create_sample_images():
    """Create sample images with text for testing OCR"""

    # Create images directory if it doesn't exist
    images_dir = os.path.join(os.path.dirname(__file__), "test_images")
    os.makedirs(images_dir, exist_ok=True)

    sample_images = []

    # Sample 1: Clean document (scanned document simulation)
    try:
        img1 = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img1)

        # Try to use a default font, fallback to default if not available
        try:
            font = ImageFont.truetype("/System/Library/Fonts/STHeiti Light.ttc", 32)
            font_small = ImageFont.truetype("/System/Library/Fonts/STHeiti Light.ttc", 24)
        except:
            font = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Draw text
        text_lines = [
            "技术文档",
            "",
            "本文档介绍人工智能的基本概念。",
            "人工智能是计算机科学的一个分支。",
            "它致力于创建智能系统。",
            "",
            "创建日期：2025年3月20日",
            "版本：v1.0"
        ]

        y = 50
        for line in text_lines:
            if line:
                draw.text((50, y), line, fill='black', font=font_small)
            y += 50

        img1_path = os.path.join(images_dir, "document_clean.png")
        img1.save(img1_path)
        sample_images.append(img1_path)
        logger.info(f"Created sample image: {img1_path}")

    except Exception as e:
        logger.warning(f"Failed to create sample image 1: {e}")

    # Sample 2: Screenshot simulation (UI text)
    try:
        img2 = Image.new('RGB', (800, 600), color='lightgray')
        draw = ImageDraw.Draw(img2)

        try:
            font = ImageFont.truetype("/System/Library/Fonts/STHeiti Light.ttc", 28)
        except:
            font = ImageFont.load_default()

        # Draw UI elements
        draw.rectangle([50, 50, 750, 150], fill='white', outline='black', width=2)
        draw.text((60, 70), "系统设置", fill='black', font=font)

        draw.rectangle([50, 200, 750, 280], fill='white', outline='black', width=2)
        draw.text((60, 220), "用户名：admin", fill='black', font=font)

        draw.rectangle([50, 320, 750, 400], fill='white', outline='black', width=2)
        draw.text((60, 340), "保存设置", fill='black', font=font)

        img2_path = os.path.join(images_dir, "screenshot_ui.png")
        img2.save(img2_path)
        sample_images.append(img2_path)
        logger.info(f"Created sample image: {img2_path}")

    except Exception as e:
        logger.warning(f"Failed to create sample image 2: {e}")

    # Sample 3: Natural scene simulation (sign/poster)
    try:
        img3 = Image.new('RGB', (800, 400), color='blue')
        draw = ImageDraw.Draw(img3)

        try:
            font_large = ImageFont.truetype("/System/Library/Fonts/STHeiti Light.ttc", 48)
            font_med = ImageFont.truetype("/System/Library/Fonts/STHeiti Light.ttc", 32)
        except:
            font_large = ImageFont.load_default()
            font_med = ImageFont.load_default()

        # Draw poster text
        draw.text((200, 100), "欢迎参加", fill='white', font=font_large)
        draw.text((150, 180), "人工智能技术峰会", fill='white', font=font_large)
        draw.text((250, 280), "2025年3月20日", fill='white', font=font_med)

        img3_path = os.path.join(images_dir, "poster_natural.png")
        img3.save(img3_path)
        sample_images.append(img3_path)
        logger.info(f"Created sample image: {img3_path}")

    except Exception as e:
        logger.warning(f"Failed to create sample image 3: {e}")

    return sample_images


def test_ocr_reader():
    """Test the ImageOCRReader with sample images"""

    print("\n" + "="*60)
    print("Testing ImageOCRReader")
    print("="*60)

    # Create sample images
    print("\nCreating sample test images...")
    sample_images = create_sample_images()

    if not sample_images:
        print("No sample images created. Please add your own images to test_images/ directory.")
        return None

    # Initialize OCR reader
    print("\nInitializing PaddleOCR...")
    reader = ImageOCRReader(lang='ch', use_gpu=False, show_log=False)

    # Test single image
    print(f"\n--- Testing Single Image ---")
    if sample_images:
        docs = reader.load_data(sample_images[0])
        if docs:
            doc = docs[0]
            print(f"\nImage: {doc.metadata['file_name']}")
            print(f"Text blocks detected: {doc.metadata['num_text_blocks']}")
            print(f"Average confidence: {doc.metadata['avg_confidence']:.4f}")
            print(f"\nExtracted text:")
            print(doc.text)

    # Test batch loading
    print(f"\n--- Testing Batch Loading ---")
    all_docs = reader.load_data(sample_images)
    print(f"\nProcessed {len(all_docs)} images")

    for i, doc in enumerate(all_docs, 1):
        print(f"\n{i}. {doc.metadata['file_name']}")
        print(f"   Blocks: {doc.metadata['num_text_blocks']}, "
              f"Confidence: {doc.metadata['avg_confidence']:.4f}")

    return all_docs


def test_llamaindex_integration(documents):
    """Test integration with LlamaIndex"""

    print("\n" + "="*60)
    print("Testing LlamaIndex Integration")
    print("="*60)

    if not documents:
        print("No documents to index")
        return

    # Create vector index
    print("\nCreating vector store index...")
    index = VectorStoreIndex.from_documents(documents)

    # Create query engine
    query_engine = index.as_query_engine(similarity_top_k=3)

    # Test queries
    test_queries = [
        "图片中提到了什么日期？",
        "文档的版本是什么？",
        "系统设置中显示的用户名是什么？",
        "峰会的主题是什么？",
    ]

    print("\n--- Testing Queries ---")
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: {query}")
        try:
            response = query_engine.query(query)
            print(f"   Response: {response}")
        except Exception as e:
            print(f"   Error: {e}")


def analyze_ocr_quality(documents):
    """Analyze OCR quality metrics"""

    print("\n" + "="*60)
    print("OCR Quality Analysis")
    print("="*60)

    if not documents:
        print("No documents to analyze")
        return

    total_blocks = 0
    confidences = []
    image_types = {
        'document': [],
        'screenshot': [],
        'poster': []
    }

    for doc in documents:
        filename = doc.metadata['file_name']
        blocks = doc.metadata['num_text_blocks']
        confidence = doc.metadata['avg_confidence']

        total_blocks += blocks
        confidences.append(confidence)

        # Categorize by filename
        if 'document' in filename:
            image_types['document'].append(confidence)
        elif 'screenshot' in filename:
            image_types['screenshot'].append(confidence)
        elif 'poster' in filename:
            image_types['poster'].append(confidence)

    # Overall statistics
    print(f"\nOverall Statistics:")
    print(f"  Total images processed: {len(documents)}")
    print(f"  Total text blocks detected: {total_blocks}")
    print(f"  Average blocks per image: {total_blocks / len(documents):.2f}")
    print(f"  Overall average confidence: {sum(confidences) / len(confidences):.4f}")

    # By image type
    print(f"\nConfidence by Image Type:")
    for img_type, confs in image_types.items():
        if confs:
            avg_conf = sum(confs) / len(confs)
            print(f"  {img_type.capitalize()}: {avg_conf:.4f} (n={len(confs)})")

    # Quality assessment
    print(f"\nQuality Assessment:")
    high_quality = sum(1 for c in confidences if c >= 0.9)
    medium_quality = sum(1 for c in confidences if 0.7 <= c < 0.9)
    low_quality = sum(1 for c in confidences if c < 0.7)

    print(f"  High quality (≥0.9): {high_quality} images")
    print(f"  Medium quality (0.7-0.9): {medium_quality} images")
    print(f"  Low quality (<0.7): {low_quality} images")


def demonstrate_use_cases():
    """Demonstrate practical use cases"""

    print("\n" + "="*60)
    print("Practical Use Cases Demonstration")
    print("="*60)

    # Use case 1: Document indexing
    print("\nUse Case 1: Document Indexing and Search")
    print("-" * 40)

    images_dir = os.path.join(os.path.dirname(__file__), "test_images")
    if os.path.exists(images_dir):
        reader = ImageOCRReader(lang='ch', use_gpu=False, show_log=False)

        # Load all images from directory
        image_files = [os.path.join(images_dir, f) for f in os.listdir(images_dir)
                      if f.endswith(('.png', '.jpg', '.jpeg'))]

        if image_files:
            docs = reader.load_data(image_files)
            print(f"Loaded {len(docs)} documents from images")

            # Create searchable index
            index = VectorStoreIndex.from_documents(docs)
            query_engine = index.as_query_engine()

            # Demonstrate search
            query = "文档中提到的所有日期"
            print(f"\nSearching for: {query}")
            response = query_engine.query(query)
            print(f"Result: {response}")


def main():
    """Main entry point"""

    print("="*60)
    print("OCR Image Text Loader for LlamaIndex")
    print("Using PaddleOCR")
    print("="*60)

    # Check API key
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("Warning: DASHSCOPE_API_KEY not found in environment")
        return

    try:
        # Test 1: OCR Reader functionality
        documents = test_ocr_reader()

        if not documents:
            print("\nNo documents extracted. Please check your images.")
            return

        # Test 2: LlamaIndex integration
        test_llamaindex_integration(documents)

        # Test 3: Quality analysis
        analyze_ocr_quality(documents)

        # Test 4: Use cases
        demonstrate_use_cases()

        print("\n" + "="*60)
        print("All tests completed!")
        print("="*60)
        print("\nNext steps:")
        print("1. Review test_images/ directory for generated samples")
        print("2. Add your own images for more comprehensive testing")
        print("3. Check report.md for detailed analysis")

    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)


if __name__ == "__main__":
    main()
