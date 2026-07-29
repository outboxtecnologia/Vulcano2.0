const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  
  // Use file protocol to open the HTML since it's locally in the designs folder
  const filePath = path.resolve('Vulcano Selecao Empresas.html');
  await page.goto(`file://${filePath}`, {
    waitUntil: 'networkidle0',
  });
  
  await new Promise(resolve => setTimeout(resolve, 5000));
  
  const html = await page.content();
  fs.writeFileSync('rendered_empresas_dom.html', html);
  
  await browser.close();
  console.log("DOM saved to rendered_empresas_dom.html");
})();
