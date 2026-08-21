import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const ARTIFACTS_DIR = 'C:\\Users\\Naveen\\.gemini\\antigravity-ide\\brain\\1cf4186b-2b78-4c7b-a29d-3a269c7b6aa8';
const SCAN_XML_PATH = 'E:\\test_rat\\AEGIS_V0.1\\backend\\tests\\data\\scan.xml';
const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

async function run() {
  console.log('Launching Chrome with puppeteer-core...');
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1440,900']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 2 });

  console.log('Navigating to http://localhost:5173 ...');
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 2000));

  // --- GATE 1: "Is CVE-2024-21626 critical?" ---
  console.log('Running Gate 1: "Is CVE-2024-21626 critical?" ...');
  // Type query and submit
  const inputSelector = 'input[placeholder*="Ask AEGIS"]';
  await page.waitForSelector(inputSelector);
  await page.type(inputSelector, 'Is CVE-2024-21626 critical?');
  await page.keyboard.press('Enter');

  console.log('Waiting for Gate 1 answer and citations...');
  // Wait until citation cards appear or answer finishes
  await page.waitForFunction(() => {
    return document.querySelectorAll('.grid .group, [class*="CitationCard"]').length > 0 ||
           document.body.innerText.includes('Verified Provenance Citations') ||
           document.body.innerText.includes('runc');
  }, { timeout: 30000 });

  await new Promise(r => setTimeout(r, 2500));

  const gate1Path = path.join(ARTIFACTS_DIR, 'gate1_cve_2024_21626_answer.png');
  await page.screenshot({ path: gate1Path, fullPage: false });
  console.log(`Gate 1 screenshot saved to ${gate1Path}`);

  // --- GATE 2: "Tell me about CVE-2099-99999" (Silence / Insufficient Evidence) ---
  console.log('Running Gate 2: "Tell me about CVE-2099-99999" ...');
  await page.type(inputSelector, 'Tell me about CVE-2099-99999');
  await page.keyboard.press('Enter');

  console.log('Waiting for Gate 2 amber silence banner...');
  await page.waitForFunction(() => {
    return document.body.innerText.includes('NO VERIFIED INTEL') ||
           document.body.innerText.includes('CITATION OR SILENCE');
  }, { timeout: 30000 });

  await new Promise(r => setTimeout(r, 2500));

  const gate2Path = path.join(ARTIFACTS_DIR, 'gate2_insufficient_evidence_banner.png');
  await page.screenshot({ path: gate2Path, fullPage: false });
  console.log(`Gate 2 screenshot saved to ${gate2Path}`);

  // --- GATE 3: Nmap Scan Tab & scan.xml Upload ---
  console.log('Running Gate 3: Nmap Scan Tab & XML correlation...');
  await page.click('#tab-scan');
  await new Promise(r => setTimeout(r, 1000));

  // Upload file to file input
  const fileInput = await page.$('input[type="file"]');
  await fileInput.uploadFile(SCAN_XML_PATH);
  await new Promise(r => setTimeout(r, 1000));

  // Click Run Sovereign Surface Analysis
  console.log('Clicking Run Sovereign Surface Analysis button...');
  const buttons = await page.$$('button');
  for (const btn of buttons) {
    const text = await page.evaluate(el => el.innerText, btn);
    if (text.includes('Run Sovereign Surface Analysis') || text.includes('Surface Analysis')) {
      await btn.click();
      break;
    }
  }

  console.log('Waiting for scan results matrix...');
  await page.waitForFunction(() => {
    return document.body.innerText.includes('HOSTS DISCOVERED') ||
           document.body.innerText.includes('MATCHED CVES') ||
           document.body.innerText.includes('Apache httpd');
  }, { timeout: 30000 });

  await new Promise(r => setTimeout(r, 3000));

  const gate3Path = path.join(ARTIFACTS_DIR, 'gate3_nmap_scan_results.png');
  await page.screenshot({ path: gate3Path, fullPage: false });
  console.log(`Gate 3 screenshot saved to ${gate3Path}`);

  await browser.close();
  console.log('All acceptance gate screenshots successfully captured!');
}

run().catch(err => {
  console.error('Error running capture script:', err);
  process.exit(1);
});
