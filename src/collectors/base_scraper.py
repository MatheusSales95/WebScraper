import time
import random
import requests
import logging
import yaml
from abc import ABC, abstractmethod

# Configuração de Logs
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class BaseScraper(ABC):
    def __init__(self, config_path='config/settings.yaml'):
        self.config = self._load_config(config_path)
        self.session = requests.Session()

    def _load_config(self, path):
        with open(path, 'r') as file:
            return yaml.safe_load(file)

    def _get_headers(self):
        # Rotaciona User-Agents para evitar bloqueio
        user_agent = random.choice(self.config['scraping']['user_agents'])
        return {'User-Agent': user_agent}

    def _wait(self):
        # Implementa Rate Limiting
        min_delay = self.config['scraping']['min_delay']
        max_delay = self.config['scraping']['max_delay']
        sleep_time = random.uniform(min_delay, max_delay)
        logging.info(f"Aguardando {sleep_time:.2f} segundos...")
        time.sleep(sleep_time)

    def fetch_page(self, url):
        # Método genérico para baixar conteúdo bruto
        self._wait()
        try:
            headers = self._get_headers()
            response = self.session.get(
                url, headers=headers, timeout=self.config['scraping']['timeout'])
            response.raise_for_status()

            # Garante a codificação correta (UTF-8 é padrão hoje em dia)
            response.encoding = response.apparent_encoding
            return response.text
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao acessar {url}: {e}")
            return None

    @abstractmethod
    def parse(self, html_content):
        # Método abstrato que cada scraper específico deve implementar
        pass
