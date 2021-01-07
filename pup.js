const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  // await page.setViewport({
  //   width: 1280,
  //   height: 720,
  //   deviceScaleFactor: 1,
  // });
  const html_path = process.argv[2]
  const image_path = process.argv[3];
  await page.goto(html_path);
  const selector = '#vid_area';
  await page.waitForSelector(selector);
  const element = await page.$(selector);  
  await element.screenshot({path: image_path});

  await browser.close();
})();