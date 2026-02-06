import re
import unicodedata


class PDFCleaner:
    # --- 1. CONFIGURAÇÃO DE PADRÕES (Modo Agressivo) ---
    REGEX_PATTERNS = {
        'structure': [
            (r'(\w+)-\s*\n\s*(\w+)', r'\1\2'),
            (r'^.*(?:\.{4,}|…{2,}).*$', ''),
            (r'^\s*\d+\s*$', ''),
            (r'--- PAGE \d+ ---', ''),
            (r'Página \d+ de \d+', ''),
        ],
        'academic_front_matter': [
            # INSTITUCIONAIS (Topo da página)
            (r'^\s*INSTITUTO FEDERAL.*', ''),
            (r'^\s*UNIVERSIDADE.*', ''),
            (r'^\s*FACULDADE.*', ''),
            (r'^\s*PRÓ-REITORIA.*', ''),
            (r'^\s*DIRETORIA DE.*', ''),
            (r'^\s*COORDENAÇÃO DE.*', ''),
            (r'^\s*CURSO DE.*', ''),
            (r'^\s*DEPARTAMENTO DE.*', ''),
            (r'^\s*PROGRAMA DE PÓS-GRADUAÇÃO.*', ''),

            # NATUREZA DO TRABALHO
            (r'^\s*TCC-Artigo apresentado.*', ''),  # Específico do seu arquivo
            (r'^\s*Trabalho de Conclusão de Curso.*', ''),
            (r'^\s*Monografia submetida.*', ''),
            (r'^\s*Dissertação.*', ''),
            (r'^\s*Tese apresentada.*', ''),
            (r'^\s*Artigo apresentado.*', ''),
            (r'^\s*Requisito para obtenção.*', ''),

            # PESSOAS E BANCA
            (r'^\s*Orientador[a]?:.*', ''),
            (r'^\s*Coorientador[a]?:.*', ''),
            (r'^\s*Banca Examinadora.*', ''),
            (r'^\s*Prof\.\s*Dr\..*', ''),
            (r'^\s*Prof\.\s*Ms\..*', ''),
            (r'^\s*Aprovado em:.*', ''),

            # ELEMENTOS PRÉ-TEXTUAIS
            (r'^\s*DEDICATÓRIA.*', ''),
            (r'^\s*AGRADECIMENTOS.*', ''),
            (r'^\s*EPÍGRAFE.*', ''),
            (r'^\s*RESUMO\s*$', ''),
            (r'^\s*ABSTRACT\s*$', ''),
            (r'^\s*LISTA DE .*', ''),
            (r'^\s*SUMÁRIO\s*$', ''),
            # Pega "CATALOGRÁFICA" e "COTALOGRÁFICA"
            (r'^\s*FICHA CA[TO]LOGRÁFICA.*', ''),
        ],
        'metadata': [
            (r'NOTA TÉCNICA.*', ''),
            (r'AMAZÔNIA EM CHAMAS.*', ''),
            (r'REFERÊNCIAS BIBLIOGRÁFICAS.*', ''),
            (r'CONSIDERAÇÕES FINAIS.*', ''),
            (r'ipam\.org\.br.*', ''),
            (r'ipam_amazonia.*', ''),
            (r'IPAMamazonia.*', ''),
            (r'IPAMclima.*', ''),
            (r'Abril de \d{4} • nº \d+', ''),
            (r'^\s*Documento Digitalizado.*', ''),  # Final do seu arquivo
            (r'^\s*Assinado digitalmente.*', ''),
        ],
        'contacts': [
            (r'(?:E-mails?:?\s*)?[\w\.-]+@[\w\.-]+\.\w+', ''),
            (r'https?://\S+', ''),
            (r'doi:?\s*10\.\S+', ''),
            (r'^.*\b\d{5}-\d{3}\b.*$', ''),
            # Remove linhas com CNPJ
            (r'^.*\bCNPJ:?\s*\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b.*$', ''),
            (r'^.*(?:Av\.|Rua|Alameda|Bloco|Sala)\s+.*$', ''),
            (r'^\s*Brasília,\s*DF.*', ''),
        ],
        'tables_and_figures': [
            (r'^(TI|UC|APA|ASR|PP|ND|SI)\s+[\d\.]+\s+[\d\.]+', ''),
            (r'^Categoria fundiária.*', ''),
            (r'.*[\d\.,]{3,}\s+[\d\.,]{3,}\s+[\d\.,]{3,}.*', ''),
            (r'\(\s*(?:ver|vide|consultar|fonte:?)?[:\s]*(?:Figura|Fig\.|Tabela|Tab\.|Quadro|Gráfico|Mapa|Imagem|Foto|Anexo)\s+[\w\d.-]+\s*\)', ''),
            (r'\b(?:Figura|Fig\.|Tabela|Tab\.|Quadro|Gráfico|Mapa|Imagem|Foto|Anexo)\s+\d+(?:[\.-]\d+)*\b', ''),
            (r'^\s*(?:Fonte|Foto|Elaboração|Organização):\s+.*$', ''),
        ],
        'citations': [
            (r'\([^\)]+\d{4}[^\)]*\)', ''),
            (r'.*Global Change Biology.*', ''),
            (r'.*Ecological Applications.*', ''),
            (r'.*Proceedings of the National Academy.*', ''),
        ],
        'navigation_junk': [
            (r'^\s*[\d\.]+\s*$', ''),
            (r'^\s*[•●-]\s*$', ''),
            (r'^\s*[IVXLCDM]+\.\s*$', ''),
            (r'^\s*CAPÍTULO\s+[IVXLCDM\d]+\s*$', ''),
        ]
    }

    # ... (Mantenha ENGLISH_STOPS e PORTUGUESE_STOPS iguais) ...
    ENGLISH_STOPS = {
        'the', 'and', 'of', 'to', 'in', 'is', 'that', 'for', 'by', 'with',
        'as', 'on', 'at', 'from', 'this', 'are', 'which', 'or', 'an', 'be',
        'we', 'our', 'abstract', 'introduction', 'results', 'discussion'
    }
    PORTUGUESE_STOPS = {
        'o', 'a', 'os', 'as', 'de', 'do', 'da', 'em', 'que', 'e', 'para',
        'com', 'não', 'uma', 'um', 'por', 'mais', 'dos', 'das', 'se',
        'resumo', 'introdução', 'resultados', 'discussão'
    }

    @staticmethod
    def _apply_regex_rules(text, pattern_group):
        """Aplica regex com flag IGNORECASE e MULTILINE para pegar âncoras ^ corretamente."""
        for pat, repl in pattern_group:
            text = re.sub(pat, repl, text, flags=re.MULTILINE | re.IGNORECASE)
        return text

    @staticmethod
    def _truncate_at_references(text):
        """
        [ATUALIZADO] Corta referências de forma mais agressiva se encontrar os cabeçalhos.
        """
        if len(text) < 1000:
            return text

        # Adicionei variações comuns em letras maiúsculas ou mistas
        end_markers = [
            r"REFERÊNCIAS BIBLIOGRÁFICAS",
            r"REFERÊNCIAS BIBLIOGRAFIAS",
            r"LITERATURA CITADA",
            r"BIBLIOGRAFIA CONSULTADA",
            r"Sugestão de citação:.*",
            r"^REFERÊNCIAS\s*$"  # Referências solto na linha
        ]
        halfway = len(text) // 2

        for marker in end_markers:
            matches = list(re.finditer(
                marker, text, flags=re.IGNORECASE | re.MULTILINE))
            if matches:
                last = matches[-1]
                if last.start() > halfway or "Sugestão de citação" in last.group():
                    return text[:last.start()]
        return text

    # ... (Mantenha _filter_content_lines e process iguais) ...
    def _filter_content_lines(self, text):
        lines = text.split('\n')
        clean_lines = []

        author_pattern = re.compile(r'^[A-ZÀ-Ú\.\s,;-]{4,}[\.,]$')
        metadata_garbage = re.compile(
            r"Acesso em:|Disponível em:|\bv\.\s*\d+|\bn\.\s*\d+|\bp\.\s*\d+|Vol\.\s*\d+|Revista|Journal|In:\s+[A-Z]|et al\.",
            re.IGNORECASE
        )

        for line in lines:
            line_str = line.strip()
            if len(line_str) < 3:
                continue

            if metadata_garbage.search(line_str):
                continue

            if author_pattern.match(line_str):
                if ',' in line_str or '.' in line_str:
                    continue

            if line_str.lower().startswith('resolução nº'):
                continue

            words = re.findall(r'\b[a-z]+\b', line_str.lower())
            if len(words) >= 3:
                eng_score = sum(1 for w in words if w in self.ENGLISH_STOPS)
                pt_score = sum(1 for w in words if w in self.PORTUGUESE_STOPS)
                if eng_score > pt_score and eng_score >= 2:
                    continue

            clean_lines.append(line)

        return " ".join(clean_lines)

    def process(self, raw_text):
        if not raw_text:
            return ""

        text = unicodedata.normalize('NFC', raw_text)

        text = self._apply_regex_rules(text, self.REGEX_PATTERNS['structure'])
        text = self._truncate_at_references(text)

        text = self._apply_regex_rules(
            text, self.REGEX_PATTERNS['academic_front_matter'])
        text = self._apply_regex_rules(text, self.REGEX_PATTERNS['metadata'])
        text = self._apply_regex_rules(text, self.REGEX_PATTERNS['contacts'])
        text = self._apply_regex_rules(
            text, self.REGEX_PATTERNS['tables_and_figures'])
        text = self._apply_regex_rules(
            text, self.REGEX_PATTERNS['navigation_junk'])

        text = self._filter_content_lines(text)
        text = self._apply_regex_rules(text, self.REGEX_PATTERNS['citations'])
        text = re.sub(r'\s+', ' ', text).strip()

        return text
