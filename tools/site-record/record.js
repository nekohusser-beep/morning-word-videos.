// Record real pages as phone-sized scroll videos (proof footage for promos).
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const jobs = JSON.parse(process.env.JOBS); // [{name,url,secs}]
  fs.mkdirSync('rec', { recursive: true });
  const browser = await chromium.launch();
  for (const j of jobs) {
    const ctx = await browser.newContext({
      viewport: { width: 432, height: 768 }, deviceScaleFactor: 2.5, isMobile: true, hasTouch: true,
      userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
      recordVideo: { dir: 'rec/raw', size: { width: 1080, height: 1920 } },
    });
    const page = await ctx.newPage();
    try {
      await page.goto(j.url, { waitUntil: 'networkidle', timeout: 60000 });
    } catch (e) { console.log('goto warn', j.name, e.message); }
    await page.waitForTimeout(2500);
    if (j.hideFixed !== false) await page.evaluate(() => {
      // hide floating badges/chat bubbles (e.g. 'Built on Wix Headless') so footage is clean
      for (const el of document.querySelectorAll('body *')) {
        const cs = getComputedStyle(el);
        if ((cs.position === 'fixed' || cs.position === 'sticky') && el.getBoundingClientRect().top > 200) el.style.display = 'none';
      }
      for (const el of document.querySelectorAll('a,div,iframe')) {
        if (/Built on\s*WIX|wix-headless|Got a job\?/i.test((el.innerText || '') + (el.id || '') + (el.className || '')) && el.getBoundingClientRect().height < 120) el.style.display = 'none';
      }
    });
    await page.screenshot({ path: `rec/${j.name}-top.png` });
    await page.screenshot({ path: `rec/${j.name}-full.png`, fullPage: true });
    const h = await page.evaluate(() => document.body.scrollHeight);
    const secs = j.secs || 12, steps = secs * 30;
    for (let i = 0; i <= steps; i++) {
      const p = i / steps, e = p < .5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
      await page.evaluate(y => window.scrollTo(0, y), Math.max(0, (h - 768)) * e);
      await page.waitForTimeout(33);
    }
    await page.waitForTimeout(800);
    const v = page.video();
    await ctx.close();
    fs.renameSync(await v.path(), `rec/${j.name}.webm`);
    console.log('done', j.name, h);
  }
  await browser.close();
})();
