import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const ARTIFACT_DIR = 'C:\\Users\\Ankit007\\.gemini\\antigravity-ide\\brain\\1b710a56-b160-46c8-88d5-f4f47b420b1a';
const EDGE_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';

async function run() {
  console.log('Launching Edge browser...');
  const browser = await puppeteer.launch({
    executablePath: EDGE_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--window-size=1440,900'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  // 1. Login Page
  console.log('1. Navigating to Login Page...');
  await page.goto('http://localhost:3000/login', { waitUntil: 'domcontentloaded' });
  await new Promise(r => setTimeout(r, 1500));
  await page.screenshot({ path: path.join(ARTIFACT_DIR, '01_login_page.png') });
  console.log('   Saved 01_login_page.png');

  // 2. Select District Role & Submit
  console.log('2. Selecting District Role...');
  const districtBtn = await page.evaluateHandle(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    return buttons.find(b => b.textContent.includes('DISTRICT') || b.textContent.includes('district'));
  });
  if (districtBtn) {
    await districtBtn.click();
    await new Promise(r => setTimeout(r, 500));
  }

  console.log('   Submitting login form...');
  const submitBtn = await page.evaluateHandle(() => {
    const buttons = Array.from(document.querySelectorAll('button[type="submit"]'));
    return buttons[0] || Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Sign In'));
  });
  if (submitBtn) {
    await submitBtn.click();
  }

  // 3. Wait for Dashboard to load
  console.log('3. Waiting for Dashboard...');
  await new Promise(r => setTimeout(r, 3000));
  await page.screenshot({ path: path.join(ARTIFACT_DIR, '02_dashboard_overview.png') });
  console.log('   Saved 02_dashboard_overview.png');

  // 4. Click on victim VIC-2024-10002
  console.log('4. Clicking on victim VIC-2024-10002...');
  const victimRow = await page.evaluateHandle(() => {
    const rows = Array.from(document.querySelectorAll('tr'));
    return rows.find(r => r.textContent.includes('VIC-2024-10002') || r.textContent.includes('10002'));
  });
  if (victimRow) {
    await victimRow.click();
  } else {
    await page.goto('http://localhost:3000/victims/VIC-2024-10002', { waitUntil: 'domcontentloaded' });
  }

  await new Promise(r => setTimeout(r, 3000));
  await page.screenshot({ path: path.join(ARTIFACT_DIR, '03_victim_detail_overview.png') });
  console.log('   Saved 03_victim_detail_overview.png');

  // 5. Scroll down in victim detail to see recommendations & check-in table
  console.log('5. Scrolling for recommendations & check-ins...');
  await page.evaluate(() => {
    const mainEl = document.querySelector('main');
    if (mainEl) {
      mainEl.scrollTop = 700;
    } else {
      window.scrollBy(0, 700);
    }
  });
  await new Promise(r => setTimeout(r, 1500));
  await page.screenshot({ path: path.join(ARTIFACT_DIR, '04_victim_recommendations_and_checkins.png') });
  console.log('   Saved 04_victim_recommendations_and_checkins.png');

  // 6. Alerts Feed
  console.log('6. Navigating to Alerts Feed...');
  await page.goto('http://localhost:3000/alerts', { waitUntil: 'domcontentloaded' });
  await new Promise(r => setTimeout(r, 2500));
  await page.screenshot({ path: path.join(ARTIFACT_DIR, '05_alerts_feed.png') });
  console.log('   Saved 05_alerts_feed.png');

  // 7. Simulation Page
  console.log('7. Navigating to Simulation Page...');
  await page.goto('http://localhost:3000/simulation', { waitUntil: 'domcontentloaded' });
  await new Promise(r => setTimeout(r, 2500));
  await page.screenshot({ path: path.join(ARTIFACT_DIR, '06_simulation_page.png') });
  console.log('   Saved 06_simulation_page.png');

  // 8. Public Chatbot Page
  console.log('8. Navigating to Public Chatbot Page...');
  await page.goto('http://localhost:3000/chatbot?vic=VIC-2024-10002', { waitUntil: 'domcontentloaded' });
  await new Promise(r => setTimeout(r, 2500));
  await page.screenshot({ path: path.join(ARTIFACT_DIR, '07_saheli_chatbot.png') });
  console.log('   Saved 07_saheli_chatbot.png');

  await browser.close();
  console.log('All screenshots captured successfully!');
}

run().catch(err => {
  console.error('Error during capture:', err);
  process.exit(1);
});
