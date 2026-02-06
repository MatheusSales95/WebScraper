import json
import os
import re
from datetime import datetime
from src.processors.cleaner import TextCleaner


class FileManager:
    def __init__(self, base_path="data"):
        self.base_path = base_path
        os.makedirs(os.path.join(self.base_path, "01_raw"), exist_ok=True)
        os.makedirs(os.path.join(self.base_path,
                    "03_processed"), exist_ok=True)
        os.makedirs(os.path.join(self.base_path,
                    "04_training_corpus"), exist_ok=True)

    def _generate_filename(self, source, extension):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{source}_{timestamp}.{extension}"

    def save_raw_json(self, data, source_name):
        filename = self._generate_filename(source_name, "json")
        filepath = os.path.join(self.base_path, "01_raw", filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"[STORAGE] Raw JSON salvo: {filename}")
        return filepath

    def save_processed_text(self, text, source_name):
        filename = self._generate_filename(source_name, "txt")
        filepath = os.path.join(self.base_path, "03_processed", filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"[STORAGE] Texto Processado salvo: {filename}")
        return filepath

    def save_corpus_for_training(self, sentences, source_name):
        """
        Salva o Corpus Final com filtragem e Logs de Alerta.
        """
        if not sentences:
            print(f"[ALERTA] Nenhuma sentença gerada para: {source_name}")
            return None

        filename = self._generate_filename(source_name + "_corpus", "txt")
        filepath = os.path.join(self.base_path, "04_training_corpus", filename)

        count = 0
        with open(filepath, 'w', encoding='utf-8') as f:
            for sent in sentences:
                clean_sent = sent.replace('\n', ' ').strip()

                # Validação:
                # 1. Deve ser narrativa válida
                # 2. Relaxamos a pontuação: aceitamos terminar em aspas ou parenteses também
                if TextCleaner.is_narrative_text(clean_sent):
                    valid_endings = ['.', '!', '?', '"', "'", ')', ':']

                    if clean_sent[-1] in valid_endings:
                        # Remove numeração inicial
                        clean_sent = re.sub(
                            r'^\d+(\.\d+)*\.?\s+', '', clean_sent)
                        f.write(clean_sent + '\n')
                        count += 1

        if count == 0:
            print(
                f"[ALERTA] Arquivo criado mas VAZIO (Filtros rejeitaram tudo): {filename}")
        else:
            print(f"[STORAGE] Corpus salvo ({count} linhas): {filename}")

        return filepath
