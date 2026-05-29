import logging
import fitz
import numpy as np

logger = logging.getLogger(__name__)
_ocr_engine = None


def get_ocr_engine():
    global _ocr_engine
    if _ocr_engine is None:
        from rapidocr_onnxruntime import RapidOCR
        logger.info("loading rapidocr for scanned pdf pages")
        _ocr_engine = RapidOCR()
    return _ocr_engine


def pixmap_to_rgb_array(pix):
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
    if pix.n >= 3:
        return img[:, :, :3]
    return img


def extract_page_text_from_image(page):
    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
    img = pixmap_to_rgb_array(pix)
    result, _ = get_ocr_engine()(img)
    if not result:
        return ""
    return "\n".join(line[1] for line in result).strip()


def extract_page_text(page):
    text = page.get_text().strip()
    if text:
        return text
    return extract_page_text_from_image(page)


def extract_pdf_text(file_path):
    doc = fitz.open(file_path)
    pages = []
    for i, page in enumerate(doc):
        page_text = extract_page_text(page)
        if page_text:
            pages.append(page_text)
        else:
            logger.warning("no text on page %s of %s", i + 1, file_path)
    doc.close()
    return "\n\n".join(pages).strip()
