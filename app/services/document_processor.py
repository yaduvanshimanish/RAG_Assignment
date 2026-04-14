import logging
import re
from typing import List, Tuple
from pypdf import PdfReader
import docx

logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_text_from_pdf(file_path: str) -> List[Tuple[str, int]]:
    pages = []
    try:
        reader = PdfReader(file_path)
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            cleaned = clean_text(text) if text else ""
            
            if not cleaned or len(cleaned) < 50:
                logger.info(f"Page {i + 1} of PDF at {file_path} seems scanned. Falling back to OCR.")
                try:
                    import pdf2image
                    import io
                    from app.services.gemini_service import extract_text_from_image
                    
                    images = pdf2image.convert_from_path(file_path, first_page=i+1, last_page=i+1)
                    if images:
                        img_byte_arr = io.BytesIO()
                        images[0].save(img_byte_arr, format='JPEG')
                        img_bytes = img_byte_arr.getvalue()
                        
                        ocr_text = extract_text_from_image(img_bytes, mime_type="image/jpeg", prompt="Extract all text from this document page accurately. Preserve structure.")
                        cleaned = clean_text(ocr_text)
                except ImportError:
                    logger.warning(f"pdf2image is not available or poppler-utils is not installed. Skipping OCR fallback for page {i+1}.")
                except Exception as e:
                    logger.warning(f"OCR fallback failed for page {i+1} of {file_path}: {e}")
            
            if cleaned:
                pages.append((cleaned, i + 1))
            else:
                logger.warning(f"Page {i + 1} of {file_path} yielded no text even after OCR fallback.")
    except Exception as e:
        logger.error(f"Error extracting text from PDF {file_path}: {e}")
        raise
    return pages

def extract_text_from_docx(file_path: str) -> List[Tuple[str, int]]:
    pages = []
    try:
        doc = docx.Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        
        current_page_text = []
        page_number = 1
        
        for i, para in enumerate(paragraphs):
            current_page_text.append(para)
            if (i + 1) % 40 == 0:
                pages.append((" ".join(current_page_text), page_number))
                current_page_text = []
                page_number += 1
                
        if current_page_text:
            pages.append((" ".join(current_page_text), page_number))
    except Exception as e:
        logger.error(f"Error extracting text from DOCX {file_path}: {e}")
        raise
    return pages

def extract_text_from_txt(file_path: str) -> List[Tuple[str, int]]:
    pages = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            
        if '\f' in content:
            raw_pages = content.split('\f')
            for i, p_text in enumerate(raw_pages):
                cleaned = clean_text(p_text)
                if cleaned:
                    pages.append((cleaned, i + 1))
        else:
            block_size = 3000
            for i in range(0, len(content), block_size):
                block_text = content[i:i+block_size]
                cleaned = clean_text(block_text)
                if cleaned:
                    pages.append((cleaned, i // block_size + 1))
    except Exception as e:
        logger.error(f"Error extracting text from TXT {file_path}: {e}")
        raise
    return pages

def extract_text_from_image_file(file_path: str) -> List[Tuple[str, int]]:
    pages = []
    try:
        import mimetypes
        from app.services.gemini_service import extract_text_from_image
        
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "image/jpeg"
            
        with open(file_path, "rb") as f:
            image_bytes = f.read()
            
        ocr_text = extract_text_from_image(image_bytes, mime_type=mime_type, prompt="Extract all text from this image precisely. Preserve any natural structure, formatting or tables as text. Do not add any conversational filler, just return the text found in the image.")
        cleaned = clean_text(ocr_text)
        if cleaned:
            pages.append((cleaned, 1))
        else:
            logger.warning(f"Image {file_path} yielded no text via OCR.")
    except Exception as e:
        logger.error(f"Error extracting text from Image {file_path}: {e}")
        raise
    return pages

def extract_text(file_path: str, file_type: str) -> List[Tuple[str, int]]:
    file_type = file_type.lower()
    if file_type == 'pdf':
        return extract_text_from_pdf(file_path)
    elif file_type in ('docx', 'doc'):
        return extract_text_from_docx(file_path)
    elif file_type in ('txt', 'md', 'rst'):
        return extract_text_from_txt(file_path)
    elif file_type in ('jpg', 'jpeg', 'png'):
        return extract_text_from_image_file(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

def chunk_text(text: str, page_number: int, chunk_size: int = 500, chunk_overlap: int = 50) -> List[Tuple[str, int]]:
    chunks = []
    cleaned = clean_text(text)
    if not cleaned:
        return chunks
        
    words = cleaned.split()
    if not words:
        return chunks
        
    step = chunk_size - chunk_overlap
    if step <= 0:
        step = 1
        
    for i in range(0, len(words), step):
        chunk_words = words[i:i + chunk_size]
        chunk_str = " ".join(chunk_words).strip()
        if chunk_str:
            chunks.append((chunk_str, page_number))
            
    return chunks

def process_document(file_path: str, file_type: str, chunk_size: int = 500, chunk_overlap: int = 50, max_pages: int = 1000) -> Tuple[List[Tuple[str, int]], int]:
    try:
        pages = extract_text(file_path, file_type)
        total_pages = len(pages)
        
        if total_pages > max_pages:
            logger.warning(f"File {file_path} exceeds {max_pages} pages ({total_pages}). Truncating.")
            pages = pages[:max_pages]
            
        all_chunks = []
        for text, page_number in pages:
            page_chunks = chunk_text(text, page_number, chunk_size, chunk_overlap)
            all_chunks.extend(page_chunks)
            
        return all_chunks, len(pages)
    except Exception as e:
        logger.error(f"Failed to process document {file_path}: {e}")
        raise
