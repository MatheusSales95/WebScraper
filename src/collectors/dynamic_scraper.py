import logging
import time
from playwright.sync_api import sync_playwright


class DynamicScraper:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def extract(self, url):
        """
        Abre a URL usando um navegador headless (Playwright),
        espera os gráficos carregarem e extrai o texto.
        """
        self.logger.info(f"[DYNAMIC] Iniciando extração via Playwright: {url}")

        try:
            with sync_playwright() as p:
                # 1. Lança o navegador (headless=True para não abrir janela visual)
                browser = p.chromium.launch(headless=True)

                # Contexto com User-Agent real para evitar bloqueios
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080}
                )

                page = context.new_page()

                # 2. Acessa a página (Timeout aumentado para 60s pois dashboards são pesados)
                page.goto(url, timeout=60000)

                # 3. Estratégia de Espera (Crucial para Dashboards)
                self.logger.info(
                    "[DYNAMIC] Aguardando carregamento da rede...")
                # Espera o tráfego de rede parar
                page.wait_for_load_state("networkidle")

                # Espera explícita extra para animações de gráficos terminarem (TerraBrasilis demora)
                self.logger.info(
                    "[DYNAMIC] Aguardando renderização dos gráficos (5s)...")
                time.sleep(5)

                # 4. Extração
                # Tenta pegar o título
                title = page.title()

                # Pega todo o texto visível no corpo da página
                # O 'inner_text' é melhor que 'content' aqui pois já vem sem tags HTML,
                # pegando o que o usuário realmente vê no painel.
                content = page.locator("body").inner_text()

                browser.close()

                if not content:
                    self.logger.warning(
                        f"[DYNAMIC] Conteúdo vazio retornado de: {url}")
                    return None

                return {
                    "url": url,
                    "title": title,
                    "content": content,
                    "source_type": "dynamic_dashboard"
                }

        except Exception as e:
            self.logger.error(
                f"[DYNAMIC] Erro crítico ao processar {url}: {str(e)}")
            return None

    # Método de compatibilidade (caso algum lugar antigo chame .parse)
    def parse(self, url):
        return self.extract(url)
