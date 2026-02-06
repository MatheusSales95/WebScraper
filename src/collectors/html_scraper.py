import requests
from bs4 import BeautifulSoup
import logging


class NewsScraper:
    def __init__(self):
        # Cabeçalhos para fingir ser um navegador real (Evita bloqueio 403/404 do Gov.br e Globo)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.google.com/'
        }

    def fetch_article(self, url):
        """
        Baixa e extrai o texto principal de uma notícia.
        """
        logging.info(f"[WEB] Baixando URL: {url}")

        try:
            # Timeout de 15s para evitar travar em sites lentos
            response = requests.get(url, headers=self.headers, timeout=15)

            if response.status_code != 200:
                logging.error(
                    f"[WEB] Erro {response.status_code} ao acessar: {url}")
                return None

            # Força a codificação correta (evita caracteres estranhos)
            response.encoding = response.apparent_encoding

            soup = BeautifulSoup(response.text, 'html.parser')

            # 1. Tenta extrair o Título (H1)
            title = soup.find('h1')
            title_text = title.get_text().strip() if title else "Sem Titulo"

            # 2. Estratégia de Extração de Texto (Hierarquia)
            # Tenta focar no conteúdo principal para evitar menus e rodapés
            content_body = soup.find('article') or \
                soup.find('main') or \
                soup.find('div', class_=lambda x: x and 'content' in x) or \
                soup

            # Pega todos os parágrafos <p> do corpo
            paragraphs = content_body.find_all('p')

            # Filtra parágrafos inúteis (muito curtos ou links de redes sociais)
            clean_paragraphs = []
            for p in paragraphs:
                text = p.get_text().strip()
                # Regra: Parágrafo deve ter pelo menos 30 caracteres para ser considerado texto de notícia
                if len(text) > 30 and "Copyright" not in text:
                    clean_paragraphs.append(text)

            full_text = "\n".join(clean_paragraphs)

            if not full_text:
                logging.warning(f"[WEB] Conteúdo vazio extraído de: {url}")
                return None

            return {
                "url": url,
                "title": title_text,
                "content": full_text,  # Chave padronizada para o main.py
                "source_type": "web_news"
            }

        except Exception as e:
            logging.error(f"[WEB] Falha crítica em {url}: {str(e)}")
            return None

    # Alias para manter compatibilidade caso algo chame .parse()
    def parse(self, url):
        return self.fetch_article(url)
