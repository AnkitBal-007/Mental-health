import puppeteer from 'puppeteer-core';
import path from 'path';

const ARTIFACT_DIR = 'C:\\Users\\Ankit007\\.gemini\\antigravity-ide\\brain\\1b710a56-b160-46c8-88d5-f4f47b420b1a';
const EDGE_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';

async function run() {
  console.log('Launching Edge browser for AI Chatbot test...');
  const browser = await puppeteer.launch({
    executablePath: EDGE_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1280,800'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });

  page.on('console', msg => console.log('BROWSER CONSOLE:', msg.text()));
  page.on('pageerror', err => console.log('BROWSER ERR:', err.message));

  console.log('Navigating to Saheli Chatbot with VIC-2024-10002...');
  await page.goto('http://localhost:3000/chatbot?vic=VIC-2024-10002', { waitUntil: 'domcontentloaded' });
  await new Promise(r => setTimeout(r, 4500)); // wait for full initial greeting

  console.log('Typing message into Chatbot input...');
  const textarea = await page.$('textarea');
  if (textarea) {
    await textarea.type('I felt really overwhelmed and scared after the court hearing yesterday', { delay: 15 });
    await new Promise(r => setTimeout(r, 500));

    console.log('Sending message...');
    const sendBtn = await page.evaluateHandle(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      return buttons.find(b => b.querySelector('svg') && !b.textContent.includes('हिंदी') && !b.textContent.includes('English'));
    });
    if (sendBtn) {
      await sendBtn.click();
    } else {
      await page.keyboard.press('Enter');
    }
    await new Promise(r => setTimeout(r, 6000)); // wait for AI reply & sentiment analysis
  }

  const screenshotPath = path.join(ARTIFACT_DIR, '08_ai_chatbot_conversation.png');
  await page.screenshot({ path: screenshotPath });
  console.log(`Saved screenshot to ${screenshotPath}`);

  await browser.close();
  console.log('Done!');
}

run().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
