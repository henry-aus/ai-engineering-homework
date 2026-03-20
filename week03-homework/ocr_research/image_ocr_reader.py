"""
ImageOCRReader: A custom LlamaIndex reader for extracting text from images using PaddleOCR.
"""

from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import Document
from paddleocr import PaddleOCR
import os
from typing import List, Union, Optional
import logging

logger = logging.getLogger(__name__)


class ImageOCRReader(BaseReader):
    """使用 PaddleOCR 从图像中提取文本并返回 Document"""

    def __init__(
        self,
        lang: str = 'ch',
        use_gpu: bool = False,
        show_log: bool = False,
        **kwargs
    ):
        """
        Initialize the ImageOCRReader.

        Args:
            lang: OCR language ('ch' for Chinese, 'en' for English, etc.)
            use_gpu: Whether to use GPU acceleration
            show_log: Whether to show PaddleOCR logs
            **kwargs: Additional parameters to pass to PaddleOCR
        """
        self.lang = lang
        self.use_gpu = use_gpu

        # Initialize PaddleOCR with optimized settings
        ocr_kwargs = {
            'lang': lang,
            'use_angle_cls': False,  # Disable angle classification for speed
            'use_doc_orientation_classify': False,
            'use_doc_unwarping': False,
            'use_textline_orientation': False,
            'show_log': show_log,
        }

        if use_gpu:
            ocr_kwargs['device'] = 'gpu'
        else:
            ocr_kwargs['device'] = 'cpu'

        # Merge with any additional kwargs
        ocr_kwargs.update(kwargs)

        try:
            self.ocr = PaddleOCR(**ocr_kwargs)
            logger.info(f"PaddleOCR initialized with lang={lang}, device={'gpu' if use_gpu else 'cpu'}")
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            raise

    def load_data(
        self,
        file: Union[str, List[str]],
        extra_info: Optional[dict] = None
    ) -> List[Document]:
        """
        从单个或多个图像文件中提取文本，返回 Document 列表

        Args:
            file: 图像路径字符串 或 路径列表
            extra_info: 额外的元数据信息

        Returns:
            List[Document]: 包含OCR提取文本的Document列表
        """
        # Convert single file to list
        if isinstance(file, str):
            files = [file]
        else:
            files = file

        documents = []

        for file_path in files:
            try:
                # Check if file exists
                if not os.path.exists(file_path):
                    logger.warning(f"File not found: {file_path}")
                    continue

                # Perform OCR
                logger.info(f"Processing image: {file_path}")
                result = self.ocr.ocr(file_path, cls=False)

                if not result or len(result) == 0 or not result[0]:
                    logger.warning(f"No text detected in {file_path}")
                    continue

                # Extract text and metadata
                # PaddleOCR returns: [[[box], (text, confidence)], ...]
                text_blocks = []
                confidences = []
                num_blocks = 0

                for line in result[0]:
                    if line and len(line) >= 2:
                        box, (text, confidence) = line[0], line[1]
                        text_blocks.append(f"[Block {num_blocks + 1}] (conf: {confidence:.2f}): {text}")
                        confidences.append(confidence)
                        num_blocks += 1

                # Combine all text blocks
                full_text = "\n".join(text_blocks)

                # Calculate average confidence
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

                # Prepare metadata
                metadata = {
                    'image_path': file_path,
                    'file_name': os.path.basename(file_path),
                    'ocr_model': 'PaddleOCR',
                    'ocr_version': 'PP-OCRv5',
                    'language': self.lang,
                    'num_text_blocks': num_blocks,
                    'avg_confidence': round(avg_confidence, 4),
                    'device': 'gpu' if self.use_gpu else 'cpu',
                }

                # Add extra info if provided
                if extra_info:
                    metadata.update(extra_info)

                # Create Document
                doc = Document(
                    text=full_text,
                    metadata=metadata,
                )

                documents.append(doc)
                logger.info(f"Successfully extracted {num_blocks} text blocks from {file_path}")

            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                continue

        return documents

    def load_data_from_dir(
        self,
        dir_path: str,
        supported_extensions: Optional[List[str]] = None,
        extra_info: Optional[dict] = None
    ) -> List[Document]:
        """
        批量处理目录中的所有图像文件

        Args:
            dir_path: 图像目录路径
            supported_extensions: 支持的图像扩展名列表
            extra_info: 额外的元数据信息

        Returns:
            List[Document]: 所有图像的Document列表
        """
        if supported_extensions is None:
            supported_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']

        if not os.path.exists(dir_path):
            raise ValueError(f"Directory not found: {dir_path}")

        # Get all image files
        image_files = []
        for filename in os.listdir(dir_path):
            ext = os.path.splitext(filename)[1].lower()
            if ext in supported_extensions:
                image_files.append(os.path.join(dir_path, filename))

        logger.info(f"Found {len(image_files)} images in {dir_path}")

        # Process all images
        return self.load_data(image_files, extra_info=extra_info)

    def extract_text_simple(self, file_path: str) -> str:
        """
        简单提取文本，只返回纯文本内容（不包含置信度信息）

        Args:
            file_path: 图像路径

        Returns:
            str: 提取的纯文本
        """
        result = self.ocr.ocr(file_path, cls=False)

        if not result or len(result) == 0 or not result[0]:
            return ""

        texts = []
        for line in result[0]:
            if line and len(line) >= 2:
                text = line[1][0]
                texts.append(text)

        return "\n".join(texts)
