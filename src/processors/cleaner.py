import re
import unicodedata


class TextCleaner:
    @staticmethod
    def fix_mojibake(text):
        """
        [NOVO] Corrige caracteres corrompidos (UTF-8 interpretado como MacRoman).
        Ex: converte '√°' de volta para 'á', '√£' para 'ã'.
        """
        replacements = {
            '√°': 'á', '√†': 'à', '√¢': 'â', '√£': 'ã', '√§': 'ä',
            '√©': 'é', '√®': 'è', '√™': 'ê', '√´': 'ë',
            '√≠': 'í', '√¨': 'ì', '√Æ': 'î', '√Ø': 'ï',
            '√≥': 'ó', '√≤': 'ò', '√¥': 'ô', '√µ': 'õ', '√∂': 'ö',
            '√∫': 'ú', '√π': 'ù', '√ª': 'û', '√º': 'ü',
            '√ß': 'ç', '√±': 'ñ',
            '√Å': 'Á', '√Ä': 'À', '√Ç': 'Â', '√É': 'Ã',
            '√â': 'É', '√à': 'È', '√ä': 'Ê',
            '√ç': 'Í', '√î': 'Î',
            '√ì': 'Ó', '√í': 'Ò', '√î': 'Ô', '√ï': 'Õ',
            '√ö': 'Ú', '√ô': 'Ù', '√õ': 'Û',
            '√á': 'Ç',
            '‚Äì': '–', '‚Äî': '—', '‚Äô': "'", '‚Äú': '"', '‚Äù': '"'
        }
        for bad, good in replacements.items():
            text = text.replace(bad, good)
        return text

    @staticmethod
    def remove_control_characters(text):
        return "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")

    @staticmethod
    def remove_html_tags(text):
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)

    @staticmethod
    def normalize_numbers(text):
        return re.sub(r'(?<=\d)\.(?=\d)', '', text)

    @staticmethod
    def fix_sticky_punctuation(text):
        text = re.sub(r':(?=[A-Z])', ': ', text)
        text = re.sub(r';(?=[A-Z])', '; ', text)
        text = re.sub(r'\)(?=[A-Z])', ') ', text)
        return text

    @staticmethod
    def separate_brazilian_states(text):
        states = [
            'ACRE', 'ALAGOAS', 'AMAPÁ', 'AMAZONAS', 'BAHIA', 'CEARÁ',
            'DISTRITO FEDERAL', 'ESPÍRITO SANTO', 'GOIÁS', 'MARANHÃO',
            'MATO GROSSO DO SUL', 'MATO GROSSO', 'MINAS GERAIS', 'PARÁ',
            'PARAÍBA', 'PARANÁ', 'PERNAMBUCO', 'PIAUÍ', 'RIO DE JANEIRO',
            'RIO GRANDE DO NORTE', 'RIO GRANDE DO SUL', 'RONDÔNIA', 'RORAIMA',
            'SANTA CATARINA', 'SÃO PAULO', 'SERGIPE', 'TOCANTINS'
        ]
        states.sort(key=len, reverse=True)
        for state in states:
            if state in text:
                text = text.replace(state, f" {state} ")
        return text

    @staticmethod
    def clean_sticky_suffixes(text):
        text = re.sub(r'(?<=\w)print\b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'(?<=\w)info\b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'(?<=\d{4})(?=\d{4})', ' ', text)
        return text

    @staticmethod
    def inject_missing_spaces(text):
        text = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text)
        text = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', ' ', text)
        text = re.sub(r'(?<=[0-9])(?=[A-Za-z])', ' ', text)
        text = re.sub(r'\.(?=[A-Z])', '. ', text)
        return text

    @staticmethod
    def remove_garbage_lines(text):
        garbage_patterns = [
            r"ipam_amazonia.*", r"IPAMamazonia.*", r"ipam\.org\.br.*",
            r"otnemuA", r"oãçudeR", r"Sugestão de referência.*",
            r"NOTA TÉCNICA.*", r"--- PAGE .* ---",
            r"http\S+", r"www\.\S+",
            r"Ouça este conteúdo", r"VEJA TAMBÉM",
            r"Notícias\s*MEIO\s*AMBIENTE", r"Por\s+WWF-Brasil",
            r'^[a-zç]+,\s+\d+\s+\d+',
            r"Brigadistas do Ibama.*?Amazonas",
            r"- •",
            r"Terra Brasilis Queimadas[\s\S]*?clicando nesta caixa\.?",
            r"Sobre Terra Brasillis[\s\S]*?Não mostrar novamente\.?",
            r"Terra Brasilis\|",
            # [NOVO] Filtros baseados no seu feedback
            r"^vide linha \d+.*",     # Remove "vide linha 13"
            r"^viAcessar material.*",  # Remove "viAcessar" (erro de OCR)
            r"Acesse o site.*",
            r"Clique aqui.*"
        ]
        for pat in garbage_patterns:
            text = re.sub(pat, "", text, flags=re.IGNORECASE | re.MULTILINE)
        return text

    @staticmethod
    def remove_journalistic_noise(text):
        dash_pattern = r'(?:-|–|—)'
        patterns = [
            rf'{dash_pattern}\s*Foto:\s*MapBiomas\s*',
            rf'{dash_pattern}?\s*Arte\s*g1',
            r'/\s*File\s*Photo', r'/\s*Reuters',
            rf'{dash_pattern}\s*Foto:\s*(?:[A-Z][\w\-/]+\s*)+(?=(\s[A-Z]|\.|\n|$))',
            r'^Foto:.*', r'^Fonte:.*'
        ]
        for pat in patterns:
            text = re.sub(pat, "", text, flags=re.IGNORECASE | re.MULTILINE)
        return text

    @staticmethod
    def remove_figure_references(text):
        text = re.sub(
            r'\s*\(\s*(ver|vide)?\s*(Figura|Fig\.|Tabela|Tab\.|Quadro|Gráfico|Anexo)\s+[\w\d\.]+\s*\)\.?', "", text, flags=re.IGNORECASE)
        patterns_loose = [r'Figura\s+\d+\.?',
                          r'Tabela\s+\d+\.?', r'Quadro\s+\d+\.?']
        for pat in patterns_loose:
            text = re.sub(pat, "", text, flags=re.IGNORECASE)
        return text

    @staticmethod
    def clean_citations(text):
        patterns = [r'^[A-ZÁÉÍÓÚÇ\s]{3,},.*', r'^\d{4}\.', r'^Vol\.\s?\d+']
        lines = text.split('\n')
        clean_lines = [l for l in lines if not any(
            re.match(p, l.strip()) for p in patterns)]
        return "\n".join(clean_lines)

    @staticmethod
    def remove_academic_noise(text):
        patterns = [r"Disponível em:.*", r"Acesso em:.*",
                    r"SUMÁRIO \d+\.", r"REFERÊNCIAS.*", r"INTRODUÇÃO \.*"]
        for pat in patterns:
            text = re.sub(pat, "", text, flags=re.IGNORECASE)
        return text

    @staticmethod
    def fix_broken_words(text):
        return re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)

    @staticmethod
    def normalize_unicode(text):
        return unicodedata.normalize('NFC', text)

    @staticmethod
    def normalize_whitespace(text):
        text = text.replace('\n', ' ')
        return " ".join(text.split())

    @staticmethod
    def repair_malformed_citations(text):
        text = re.sub(r'(?<=[a-z])et al\.', ' et al.', text)
        return text

    @staticmethod
    def remove_sidebar_intrusions(text):
        text = re.sub(r'(?<=[a-z])\s*[•●-]\s*', '. ', text)
        text = text.replace('•', '').replace('●', '')
        return text

    @staticmethod
    def is_narrative_text(line):
        line = line.strip()
        if not line:
            return False

        # Filtros de exclusão
        if re.match(r'^(Figura|Tabela|Quadro|Fonte:|Lista dos?|Foto:)\s+', line, re.IGNORECASE):
            return False

        # Filtro de Mojibake grave (se tiver muitos √, deleta a linha)
        if line.count('√') > 3:
            return False

        english_ref_keywords = ['journal', 'nature', 'science',
                                'research', 'vol.', 'pp.', 'doi:', 'university']
        if sum(1 for w in english_ref_keywords if w in line.lower()) >= 2:
            return False

        digit_count = sum(c.isdigit() for c in line)
        if len(line) > 0 and (digit_count / len(line)) > 0.40:
            return False

        if len(line.split()) < 4:
            return False

        return True

    def process(self, raw_text):
        if not raw_text:
            return ""

        # 1. Sanitização Básica
        text = self.fix_mojibake(raw_text)  # <--- APLICADO LOGO NO INÍCIO
        text = self.remove_control_characters(text)
        text = self.remove_html_tags(text)
        text = self.normalize_unicode(text)

        # 2. Estrutura
        text = self.fix_broken_words(text)
        text = self.normalize_numbers(text)

        # 3. Limpeza de Conteúdo
        text = self.remove_journalistic_noise(text)
        text = self.remove_figure_references(text)
        text = self.remove_garbage_lines(text)
        text = self.clean_citations(text)
        text = self.remove_academic_noise(text)

        # 4. Correções Específicas
        text = self.repair_malformed_citations(text)
        text = self.remove_sidebar_intrusions(text)

        # 5. Finalização
        text = self.clean_sticky_suffixes(text)
        text = self.fix_sticky_punctuation(text)
        text = self.separate_brazilian_states(text)
        text = self.inject_missing_spaces(text)

        text = text.replace("Map Biomas", "MapBiomas")
        text = text.replace("You Tube", "YouTube")

        replacements = {'“': '"', '”': '"',
                        "‘": "'", "’": "'", '–': '-', '—': '-'}
        for k, v in replacements.items():
            text = text.replace(k, v)

        text = self.normalize_whitespace(text)
        return text
