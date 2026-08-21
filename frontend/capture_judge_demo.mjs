import puppeteer from 'puppeteer-core';
import path from 'path';

const ARTIFACTS_DIR = 'C:\\Users\\Naveen\\.gemini\\antigravity-ide\\brain\\1cf4186b-2b78-4c7b-a29d-3a269c7b6aa8';
const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

async function run() {
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1440,900']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 2 });

  page.on('console', msg => console.log('BROWSER CONSOLE:', msg.type(), msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));

  await page.goto('http://localhost:5173', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1500));

  const inputSelector = 'input[placeholder*="Ask AEGIS"]';
  await page.waitForSelector(inputSelector);
  await page.type(inputSelector, 'Is CVE-2024-21626 critical?');
  await page.keyboard.press('Enter');

  console.log('Submitted query. Waiting for response in UI...');
  await new Promise(r => setTimeout(r, 6000));

  const step1Path = path.join(ARTIFACTS_DIR, 'judge_demo_step1_query_and_citations.png');
  await page.screenshot({ path: step1Path, fullPage: false });
  console.log(`Step 1 screenshot saved to: ${step1Path}`);

  // Click the first citation card to open deep-dive drawer / modal
  console.log('Opening citation drawer modal...');
  const citationCards = await page.$$('.grid .group, [class*="group"]');
  if (citationCards.length > 0) {
    await citationCards[0].click();
    await new Promise(r => setTimeout(r, 1500));
  }

  const step2Path = path.join(ARTIFACTS_DIR, 'judge_demo_step2_citation_modal.png');
  await page.screenshot({ path: step2Path, fullPage: false });
  console.log(`Step 2 screenshot saved to: ${step2Path}`);

  await browser.close();
  console.log('Clean judge demo captured successfully!');
}

run().catch(err => {
  console.error('Error running judge demo:', err);
  process.exit(1);
});
