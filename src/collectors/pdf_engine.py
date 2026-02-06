import fitz  # PyMuPDF
import pytesseract
import logging
import os
from pdf2image import convert_from_path
from datetime import date


class PDFEngine:
    def __init__(self):
        # Configura o Tesseract para português
        self.ocr_lang = 'por'

    def _extract_text_with_layout(self, page):
        """
        Extrai texto respeitando colunas (Blocos).
        Retorna o texto ou string vazia se for imagem.
        """
        # get_text("blocks") retorna: (x0, y0, x1, y1, "texto", block_no, block_type)
        blocks = page.get_text("blocks")

        # Ordena os blocos: Primeiro de cima para baixo (y0), depois da esquerda para a direita (x0)
        # Isso resolve o problema de ler colunas misturadas
        blocks.sort(key=lambda b: (b[1], b[0]))

        full_text = []
        for b in blocks:
            # O índice 4 é o conteúdo de texto do bloco
            text_content = b[4].strip()
            if text_content:
                full_text.append(text_content)

        return "\n".join(full_text)

    def _extract_with_ocr(self, pdf_path, page_number):
        """
        Fallback: Usa OCR se o PDF for uma imagem escaneada.
        """
        try:
            # Converte APENAS a página atual para imagem (economiza memória)
            images = convert_from_path(
                pdf_path, first_page=page_number+1, last_page=page_number+1)
            if images:
                # Roda OCR na imagem
                return pytesseract.image_to_string(images[0], lang=self.ocr_lang)
        except Exception as e:
            logging.error(
                f"[PDF ENGINE] Erro no OCR da página {page_number}: {e}")
        return ""

    def parse(self, filepath):
        if not os.path.exists(filepath):
            logging.error(f"Arquivo não encontrado: {filepath}")
            return None

        logging.info(f"[PDF ENGINE] Processando: {os.path.basename(filepath)}")

        full_content = []
        metadata = {}

        try:
            doc = fitz.open(filepath)
            metadata = doc.metadata

            total_pages = len(doc)

            for i, page in enumerate(doc):
                # 1. Tentativa Rápida (Layout Extraction)
                text = self._extract_text_with_layout(page)

                # 2. Validação: Se a página tiver menos de 50 caracteres, provavelmente é imagem/escaneada
                if len(text) < 50:
                    logging.info(
                        f"[PDF ENGINE] Pag {i+1}/{total_pages} parece imagem. Ativando OCR...")
                    text = self._extract_with_ocr(filepath, i)

                if text:
                    # Adiciona marcador de página para ajudar na depuração
                    full_content.append(f"--- PAGE {i+1} ---")
                    full_content.append(text)

            doc.close()

            raw_text = "\n".join(full_content)

            if not raw_text:
                logging.warning(
                    f"[PDF ENGINE] Nenhum texto extraído de {filepath} (nem com OCR).")
                return None

            return {
                "title": metadata.get('title', os.path.basename(filepath)),
                "author": metadata.get('author', 'Unknown'),
                "date": metadata.get('creationDate', date.today().isoformat()),
                "source_type": "pdf_document",
                "filename": os.path.basename(filepath),
                "raw_content": raw_text
            }

        except Exception as e:
            logging.error(f"[PDF ENGINE] Falha crítica ao abrir PDF: {e}")
            return None
