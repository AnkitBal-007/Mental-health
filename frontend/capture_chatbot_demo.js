import puppeteer from 'puppeteer-core';
import path from 'path';

const ARTIFACT_DIR = 'C:\\Users\\Ankit007\\.gemini\\antigravity-ide\\brain\\1b710a56-b160-46c8-88d5-f4f47b420b1a';
const EDGE_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';

async function run() {
  console.log('Launching Edge browser...');
  const browser = await puppeteer.launch({
    executablePath: EDGE_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--window-size=1200,850'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1200, height: 850 });

  page.on('console', msg => console.log('BROWSER CONSOLE:', msg.type(), msg.text()));
  page.on('pageerror', err => console.log('BROWSER PAGE ERROR:', err));

  console.log('Navigating to Saheli Didi Chatbot...');
  await page.goto('http://localhost:3000/chatbot', { waitUntil: 'domcontentloaded' });
  await new Promise(r => setTimeout(r, 2000));

  // Find 'Begin Check-In' button
  console.log('Clicking Begin Check-In button...');
  const beginBtn = await page.evaluateHandle(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    return buttons.find(b => b.textContent.includes('Begin Check-In') || b.textContent.includes('Start'));
  });
  if (beginBtn && beginBtn.asElement()) {
    await beginBtn.click();
    await new Promise(r => setTimeout(r, 1500));
  }

  // Type a distressed message seeking help
  console.log('Typing message into chat input...');
  await page.waitForSelector('textarea', { timeout: 5000 });
  const textarea = await page.$('textarea');
  if (textarea) {
    await textarea.type('दीदी मुझे बहुत डर लग रहा है, उसने मुझे फिर से धमकी दी है। मुझे समझ नहीं आ रहा मैं क्या करूँ, प्लीज मेरी मदद करो', { delay: 15 });
    await new Promise(r => setTimeout(r, 500));

    // Press Enter to send
    await page.keyboard.press('Enter');

    console.log('Waiting for Gemini AI Elder Sister response...');
    await new Promise(r => setTimeout(r, 9000));
  }

  await page.screenshot({ path: path.join(ARTIFACT_DIR, '08_didi_chatbot_consolation.png') });
  console.log('Saved 08_didi_chatbot_consolation.png');

  await browser.close();
}

run().catch(console.error);
