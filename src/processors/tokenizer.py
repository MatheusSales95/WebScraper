import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
import string
import re
import logging


class NLTKTokenizer:
    def __init__(self, language='portuguese'):
        self.language = language
        self._download_resources()
        self.stop_words = set(stopwords.words(self.language))

        # palavras comuns em slides acadêmicos que não agregam valor
        self.stop_words.update(
            ['figura', 'tabela', 'imagem', 'exemplo', 'page', 'ocr'])

        self.punctuation = set(string.punctuation)
        self.punctuation.update(['“', '”', '—', '–', '...', '``', "''", '"'])

    def _download_resources(self):
        resources = ['punkt', 'stopwords', 'punkt_tab']
        for res in resources:
            try:
                nltk.data.find(f'tokenizers/{res}')
            except LookupError:
                nltk.download(res, quiet=True)

    def tokenize_sentences(self, text):
        if not text:
            return []
        return sent_tokenize(text, language=self.language)

    def has_content(self, word):
        """
        Verifica se a palavra tem pelo menos uma letra.
        Evita tokens como '123', '..', ')' ou simbolos matemáticos isolados.
        """
        return re.search(r'[a-zA-Zá-úÁ-ÚçÇ]', word) is not None

    def process_corpus(self, text):
        if not text:
            return None

        sentences = self.tokenize_sentences(text)
        tokens_raw = word_tokenize(text.lower(), language=self.language)

        tokens_clean = []
        for word in tokens_raw:
            # Filtro 1: Stopwords e Pontuação exata
            if word in self.stop_words or word in self.punctuation:
                continue

            # Filtro 2: Tamanho mínimo (evita erros de OCR como 'e', 'o' soltos, exceto 'a'/'e' conectivos que já são stopwords)
            if len(word) < 2:
                continue

            # Filtro 3: Deve conter letras (elimina números puros e sujeira de pontuação)
            if self.has_content(word):
                tokens_clean.append(word)

        freq_dist = FreqDist(tokens_clean)

        return {
            "total_sentences": len(sentences),
            "total_tokens_raw": len(tokens_raw),
            "total_tokens_clean": len(tokens_clean),
            "unique_words": len(freq_dist),
            "lexical_richness": len(tokens_clean) / len(tokens_raw) if tokens_raw else 0,
            "top_terms": freq_dist.most_common(20),
            "sentences_sample": sentences[:3],
            "tokens_clean": tokens_clean
        }
