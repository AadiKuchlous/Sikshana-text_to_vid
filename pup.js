const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  const html_path = process.argv[2]
  const image_path = process.argv[3];
  await page.goto(html_path);
  await page.screenshot({path: image_path});

  await browser.close();
})();