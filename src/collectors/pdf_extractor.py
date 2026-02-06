import pdfplumber
import logging
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from src.collectors.base_scraper import BaseScraper


class PDFExtractor(BaseScraper):
    def __init__(self, config_path='config/settings.yaml'):
        super().__init__(config_path)

        # Para PDFs de imagens de alta resolução. O Pillow limita o tamanho
        # remover esse limite para processar slides gigantes.
        Image.MAX_IMAGE_PIXELS = None

    def _extract_via_ocr(self, file_path):

        # FALLBACK: Converte PDF em Imagem e usa Tesseract para ler. Otimizado para performance (DPI ajustado).

        logging.info(f"[OCR] Acionando leitura óptica para: {file_path}")
        text_content = ""
        try:
            # --- OTIMIZAÇÃO DE PERFORMANCE ---
            # Reduzir de 300 para 200 DPI.
            # e consome metade da memória RAM.
            images = convert_from_path(file_path, dpi=200)

            for i, image in enumerate(images):
                # Extrai texto da imagem usando Português
                # O parâmetro config='--psm 1' ajuda em páginas com layout complexo (slides)
                page_text = pytesseract.image_to_string(image, lang='por')
                text_content += f"\n--- PAGE {i+1} (OCR) ---\n{page_text}"

            return text_content
        except Exception as e:
            logging.error(f"[OCR] Falha crítica no arquivo {file_path}: {e}")
            return ""

    def parse(self, file_path):

        # Estratégia Híbrida: Texto Nativo -> Fallback OCR

        logging.info(f"Iniciando extração do PDF: {file_path}")
        full_text = ""
        metadata = {}

        try:
            # TENTATIVA 1: Extração Rápida (Camada de Texto)
            with pdfplumber.open(file_path) as pdf:
                metadata = pdf.metadata
                for i, page in enumerate(pdf.pages):
                    extracted = page.extract_text()
                    if extracted:
                        full_text += f"\n--- PAGE {i+1} ---\n{extracted}"

            # Se tiver menos de 50 caracteres úteis, assumimos que é imagem.
            if len(full_text.strip()) < 50:
                logging.warning(
                    f"Texto nativo insuficiente ({len(full_text)} chars). Tentando OCR...")
                full_text = self._extract_via_ocr(file_path)

            if not full_text.strip():
                logging.error(
                    "Falha: Nenhum texto extraído (nem nativo, nem OCR).")
                return None

            return {
                "title": metadata.get('Title', 'Relatorio_Tecnico') if metadata else "Desconhecido",
                "author": metadata.get('Author', 'Desconhecido') if metadata else "Desconhecido",
                "raw_content": full_text,
                "source_type": "pdf",
                "original_file": file_path
            }

        except Exception as e:
            logging.error(f"Erro ao processar PDF {file_path}: {e}")
            return None
