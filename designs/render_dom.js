const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  
  // Point to the local server we started earlier on port 8081
  await page.goto('http://localhost:8081/Vulcano%20Vendas%20(1).html', {
    waitUntil: 'networkidle0',
  });
  
  // Wait a bit more just in case the bundler needs time to unpack
  await new Promise(resolve => setTimeout(resolve, 5000));
  
  const html = await page.content();
  fs.writeFileSync('rendered_dom.html', html);
  
  await browser.close();
  console.log("DOM saved to rendered_dom.html");
})();
