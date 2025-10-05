# pdf_extractor.py

import fitz  # PyMuPDF
import re
from PIL import Image
import io

def analyze_and_extract_with_instructions(pdf_path: str):
    """
    Extracts questions, options, images, and full section instruction blocks from a PDF.
    Returns a list of dictionaries, where each dict represents a question.
    """
    question_pattern = re.compile(r"^\s*Q\.\s*(\d{1,3})\b")
    option_pattern = re.compile(r"^\s*\((?P<option>[A-Da-d])\)\s*(?P<text>.*)")

    doc = fitz.open(pdf_path)
    questions = []
    
    current_section_instructions = "No section instructions found before the first question."
    current_question_data = None
    unclaimed_text_buffer = []

    def finalize_question(q_data, page):
        """Placeholder for image processing. For now, we just count them."""
        if not q_data or "bbox" not in q_data: return
        
        # This part can be expanded later to save and link images.
        # For now, we are focusing on the text-to-JSON pipeline.
        image_count = 0
        page_images = page.get_images(full=True)
        for img_item in page_images:
            img_bbox = page.get_image_bbox(img_item)
            if q_data["bbox"].intersects(img_bbox):
                image_count += 1
        q_data["image_count"] = image_count # Store the count for now
        del q_data["bbox"]

    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict", sort=True)["blocks"]
        
        for block in blocks:
            if "lines" not in block: continue
            block_text = "".join(s["text"] for line in block["lines"] for s in line["spans"]).strip()
            if not block_text: continue

            question_match = question_pattern.match(block_text)
            option_match = option_pattern.match(block_text)

            if question_match:
                if current_question_data:
                    finalize_question(current_question_data, doc.load_page(current_question_data["page_num"]))
                    questions.append(current_question_data)

                if unclaimed_text_buffer:
                    current_section_instructions = "\n".join(unclaimed_text_buffer).strip()
                    unclaimed_text_buffer = []

                q_num = int(question_match.group(1))
                q_text = question_pattern.sub("", block_text, 1).strip()
                current_question_data = {
                    "question_number": q_num,
                    "section_instructions": current_section_instructions,
                    "text": q_text,
                    "options": {}, "image_count": 0,
                    "bbox": fitz.Rect(block["bbox"]), "page_num": page_num
                }

            elif current_question_data and option_match:
                if unclaimed_text_buffer:
                    current_question_data["text"] += "\n" + "\n".join(unclaimed_text_buffer).strip()
                    unclaimed_text_buffer = []
                
                opt_letter = option_match.group("option").upper()
                opt_text = option_match.group("text").strip()
                current_question_data["options"][opt_letter] = opt_text
                current_question_data["bbox"].include_rect(fitz.Rect(block["bbox"]))

            else:
                unclaimed_text_buffer.append(block_text)

    if current_question_data:
        if unclaimed_text_buffer:
             current_question_data["text"] += "\n" + "\n".join(unclaimed_text_buffer).strip()
        finalize_question(current_question_data, doc.load_page(current_question_data["page_num"]))
        questions.append(current_question_data)

    doc.close()
    return questions