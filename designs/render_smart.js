const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  
  const filePath = path.resolve('Smart Importer.html');
  await page.goto('file:///' + filePath.replace(/\\/g, '/'), {
    waitUntil: 'networkidle0',
  });
  
  await new Promise(resolve => setTimeout(resolve, 5000));
  
  const html = await page.content();
  fs.writeFileSync('rendered_smart_dom.html', html);
  
  await browser.close();
  console.log("DOM saved to rendered_smart_dom.html");
})();
