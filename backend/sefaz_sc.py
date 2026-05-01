import asyncio
import os
from playwright.async_api import async_playwright

async def baixar_relatorios_sat(cnpj: str, data_inicial: str, data_final: str, download_dir: str = "./downloads"):
    # Garante que a pasta de downloads existe
    os.makedirs(download_dir, exist_ok=True)
    
    async with async_playwright() as p:
        # Iniciando o Chrome de forma visível (headless=False)
        browser = await p.chromium.launch(headless=False, slow_mo=50)
        
        # Cria o contexto permitindo downloads
        context = await browser.new_context(
            viewport={'width': 1366, 'height': 768},
            accept_downloads=True
        )
        page = await context.new_page()

        print("1. Acessando a página de login da Sefaz SC...")
        await page.goto("https://sat.sef.sc.gov.br/tax.NET/Login.aspx")

        print("2. Preenchendo as credenciais...")
        await page.locator("#Body_pnlMain_rptLoginPanels_tbxUsername_0").fill("29981476900")
        await page.locator("#Body_pnlMain_rptLoginPanels_tbxUserPassword_0").fill("arquivo2")

        print("3. Clicando em Entrar...")
        await page.locator("#Body_pnlMain_rptLoginPanels_btnLogin_0").click()
        await page.wait_for_load_state('networkidle')

        print("4. Navegando para 'NFe / NFCe - Consulta'...")
        # Clica no link apontado no passo 1
        await page.locator("a:has-text('NFe / NFCe - Consulta')").first.click()
        await page.wait_for_load_state('networkidle')

        print("5. Preenchendo os filtros de consulta (Passo 2)...")
        # Se for preciso interagir com o Select2 de "Tipo de Documento", usaremos a UI do dropdown
        # Mas para CNPJ e Datas os IDs são fixos:
        await page.locator("#Body_Main_Main_sepConsultaNfpe_ctl10_idnEmitente_MaskedField").fill(cnpj)
        await page.locator("#Body_Main_Main_sepConsultaNfpe_datDataInicial").fill(data_inicial)
        await page.locator("#Body_Main_Main_sepConsultaNfpe_datDataFinal").fill(data_final)

        print("6. Clicando em Buscar...")
        await page.locator("#Body_Main_Main_sepConsultaNfpe_btnBuscar").click()
        await page.wait_for_timeout(2000) # Pequena pausa para a tabela carregar

        print("7. Clicando em Exportar...")
        await page.locator("#Body_Main_Main_sepConsultaNfpe_btnExportar").click()
        # O sistema gera a solicitação. Vamos aguardar um pouco.
        await page.wait_for_timeout(3000)

        print("8. Indo para 'Manutenção das Solicitações' (Passo 3)...")
        await page.locator("a:has-text('Manutenção das Solicitações de Exportação')").first.click()
        await page.wait_for_load_state('networkidle')

        print("9. Baixando o arquivo da primeira linha (Passo 4)...")
        # Aguarda o botão de download ficar visível na primeira linha da tabela
        download_btn = page.locator("a[title='Baixar o arquivo resultante'], #Body_Main_ctl00_grpSolicitacoes_gridView_cmd2_0").first
        await download_btn.wait_for(state="visible")
        
        # Intercepta o evento de download do Playwright
        async with page.expect_download() as download_info:
            await download_btn.click()
        
        # Salva o arquivo na pasta ./downloads
        download = await download_info.value
        file_path = os.path.join(download_dir, download.suggested_filename)
        await download.save_as(file_path)
        
        print(f"Sucesso! Relatório baixado e salvo em: {os.path.abspath(file_path)}")
        
        await browser.close()

if __name__ == "__main__":
    # EXEMPLO DE USO:
    asyncio.run(baixar_relatorios_sat(
        cnpj="00000000000000", # INSIRA AQUI UM CNPJ VÁLIDO PARA O TESTE
        data_inicial="01/04/2026",
        data_final="30/04/2026"
    ))
