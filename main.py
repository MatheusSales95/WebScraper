import os
import json
import logging
import argparse
import sys

# --- 1. IMPORTAÇÕES DE COLETORES (CORRIGIDO) ---
# Importa direto do html_scraper, sem try/except confuso
from src.collectors.html_scraper import NewsScraper
from src.collectors.dynamic_scraper import DynamicScraper
from src.collectors.pdf_engine import PDFEngine

# --- 2. IMPORTAÇÕES DE PROCESSADORES ---
from src.processors.cleaner import TextCleaner
from src.processors.pdf_cleaner import PDFCleaner
from src.processors.tokenizer import NLTKTokenizer
from src.processors.corpus_compiler import CorpusCompiler  # <--- NOVO
from src.storage.file_manager import FileManager

# Configuração de Logs
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - [%(levelname)s] - %(message)s')


class PipelineController:
    def __init__(self):
        # Ferramentas de Processamento
        self.web_cleaner = TextCleaner()
        self.pdf_cleaner = PDFCleaner()
        self.tokenizer = NLTKTokenizer(language='portuguese')
        self.compiler = CorpusCompiler()  # <--- NOVO
        self.storage = FileManager()

        # Coletores
        self.news_scraper = NewsScraper()
        self.dynamic_scraper = DynamicScraper()
        self.pdf_engine = PDFEngine()

    def run_pdf_mode(self):
        logging.info(">>> MODO PDF INICIADO")
        INPUT_DIR = "data/inputs"
        if not os.path.exists(INPUT_DIR):
            logging.warning(f"Pasta {INPUT_DIR} não existe.")
            return

        files = [f for f in os.listdir(
            INPUT_DIR) if f.lower().endswith('.pdf')]

        for filename in files:
            filepath = os.path.join(INPUT_DIR, filename)
            source_name = os.path.splitext(filename)[0].replace(" ", "_")

            raw_data = self.pdf_engine.parse(filepath)

            if raw_data:
                self.storage.save_raw_json(raw_data, source_name)
                # PDF usa o Cleaner Específico
                clean_text = self.pdf_cleaner.process(raw_data['raw_content'])
                sentences = self.tokenizer.tokenize_sentences(clean_text)
                self.storage.save_corpus_for_training(sentences, source_name)
                logging.info(
                    f"PDF Processado: {source_name} | {len(sentences)} sentenças")

    def run_web_mode(self):
        logging.info(">>> MODO WEB NEWS INICIADO")
        SOURCES_FILE = "config/sources.json"

        if not os.path.exists(SOURCES_FILE):
            logging.error(f"Arquivo {SOURCES_FILE} não encontrado.")
            return

        try:
            with open(SOURCES_FILE, 'r') as f:
                data = json.load(f)
                urls = data.get('news_urls', [])
        except Exception as e:
            logging.error(f"Erro ao ler JSON: {e}")
            return

        logging.info(f"Processando {len(urls)} URLs...")

        for url in urls:
            # Web usa fetch_article do html_scraper
            raw_data = self.news_scraper.fetch_article(url)

            if raw_data and raw_data.get('content'):
                slug = url.split(
                    '/')[-1][:30].replace('.html', '').replace('.ghtml', '')
                domain = url.split(
                    '//')[-1].split('/')[0].replace('www.', '').replace('.', '_')
                source_name = f"WEB_{domain}_{slug}"

                self.storage.save_raw_json(raw_data, source_name)
                # Web usa o Cleaner Geral
                clean_text = self.web_cleaner.process(raw_data['content'])
                sentences = self.tokenizer.tokenize_sentences(clean_text)

                if sentences:
                    self.storage.save_corpus_for_training(
                        sentences, source_name)
                    logging.info(
                        f"WEB Sucesso: {source_name} | {len(sentences)} sentenças")
                else:
                    logging.warning(f"Texto vazio após limpeza: {source_name}")

    def run_dynamic_mode(self):
        logging.info(">>> MODO DYNAMIC INICIADO")
        target_url = "https://terrabrasilis.dpi.inpe.br/app/dashboard/fires/biomes/aggregated/"

        # Dashboard usa extract do dynamic_scraper
        raw_data = self.dynamic_scraper.extract(target_url)

        if raw_data:
            source_name = "DASH_INPE_TerraBrasilis"
            self.storage.save_raw_json(raw_data, source_name)
            clean_text = self.web_cleaner.process(raw_data['content'])
            sentences = self.tokenizer.tokenize_sentences(clean_text)
            self.storage.save_corpus_for_training(sentences, source_name)
            logging.info(f"DASHBOARD Processado: {len(sentences)} sentenças")

    # --- NOVO MODO: COMPILAÇÃO ---
    def run_compile_mode(self):
        logging.info(">>> MODO COMPILAÇÃO INICIADO")

        # Onde estão os arquivos picados (sentenças)
        input_dir = "data/04_training_corpus"

        # Onde salvar o arquivo finalzão
        output_file = "data/05_final_dataset/corpus_queimadas_completo.txt"

        self.compiler.compile(input_dir, output_file)


def main():
    parser = argparse.ArgumentParser(description="DescrEVE Data Pipeline")

    parser.add_argument(
        '--mode',
        choices=['pdf', 'web', 'dynamic', 'all', 'compile'],
        required=True,
        help="Modos: pdf, web, dynamic, all (coleta tudo) ou compile (gera dataset final)."
    )

    args = parser.parse_args()
    controller = PipelineController()

    if args.mode == 'pdf':
        controller.run_pdf_mode()
    elif args.mode == 'web':
        controller.run_web_mode()
    elif args.mode == 'dynamic':
        controller.run_dynamic_mode()
    elif args.mode == 'all':
        controller.run_pdf_mode()
        controller.run_web_mode()
        controller.run_dynamic_mode()
    elif args.mode == 'compile':
        controller.run_compile_mode()


if __name__ == "__main__":
    main()
