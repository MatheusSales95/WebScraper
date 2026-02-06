import os
import logging
from src.processors.cleaner import TextCleaner


class CorpusCompiler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        self.DOMAIN_KEYWORDS = [

            "queimada", "incêndio", "fogo", "foco de calor", "focos", "chamas",
            "ignição", "combustão",

            "satélite", "monitoramento", "sensor", "detecção",
            "inpe", "deter", "prodes", "terrabrasilis", "mapbiomas", "nasa",
            "aqua", "terra", "noaa", "goes", "viirs", "modis", "bdqueimadas",

            "amazônia", "cerrado", "pantanal", "mata atlântica", "caatinga", "pampa",
            "bioma", "floresta", "vegetação"
        ]

    def _is_relevant(self, text):

        text_lower = text.lower()
        for keyword in self.DOMAIN_KEYWORDS:
            if keyword in text_lower:
                return True
        return False

    def compile(self, input_dir, output_file):

        if not os.path.exists(input_dir):
            self.logger.error(
                f"Diretório de entrada não encontrado: {input_dir}")
            return

        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        all_sentences = []
        seen_sentences = set()

        total_files = 0
        discarded_count = 0

        self.logger.info(
            f"Iniciando compilação SEQUENCIAL (Sem Shuffle) em: {input_dir}")

        files = sorted([f for f in os.listdir(
            input_dir) if f.endswith(".txt")])

        for filename in files:
            filepath = os.path.join(input_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines:
                        clean_line = line.strip()
                        clean_line = TextCleaner.fix_mojibake(clean_line)
                        if "vide linha" in clean_line.lower():
                            continue
                        if len(clean_line) < 20:
                            continue
                        if clean_line in seen_sentences:
                            continue
                        if self._is_relevant(clean_line):
                            seen_sentences.add(clean_line)
                            all_sentences.append(clean_line)
                        else:
                            discarded_count += 1

                total_files += 1
            except Exception as e:
                self.logger.warning(f"Erro ao ler {filename}: {e}")

        final_corpus = all_sentences

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for sentence in final_corpus:
                    f.write(sentence + "\n")

            # Estatísticas
            total_sentences = len(final_corpus)
            total_words = sum(len(s.split()) for s in final_corpus)

            print("\n" + "="*40)
            print(f"RELATÓRIO DE COMPILAÇÃO (ORDEM ORIGINAL)")
            print("="*40)
            print(f"Arquivos processados: {total_files}")
            print(f"Sentenças DESCARTADAS: {discarded_count}")
            print(f"Sentenças MANTIDAS:    {total_sentences}")
            print(f"Total de palavras:     {total_words}")
            print(f"Arquivo salvo em:      {output_file}")
            print("="*40 + "\n")

        except Exception as e:
            self.logger.error(f"Erro ao salvar arquivo final: {e}")
