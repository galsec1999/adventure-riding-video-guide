#!/usr/bin/env node
/**
 * Visual and interaction QA for the verified Chris Birch Adventure release.
 * Document version: 1.2.0
 */

const fs = require("node:fs");
const net = require("node:net");
const path = require("node:path");
const { spawn } = require("node:child_process");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..");
const OUT = path.join(ROOT, "reports", "chris-birch-v3.4", "browser-qa");
const SCREENSHOTS = path.join(OUT, "screenshots");

function freePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const { port } = server.address();
      server.close(() => resolve(port));
    });
  });
}

async function waitForServer(url) {
  let lastError;
  for (let index = 0; index < 60; index += 1) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error(`Local server did not start: ${lastError}`);
}

function chromePath() {
  const candidates = [
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    `${process.env.LOCALAPPDATA || "C:/Users/Default/AppData/Local"}/Google/Chrome/Application/chrome.exe`,
    "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
  ];
  return candidates.find((candidate) => fs.existsSync(candidate));
}

async function scenario(browser, baseUrl, config) {
  const context = await browser.newContext({
    viewport: config.viewport,
    colorScheme: "light",
    locale: "he-IL",
  });
  const page = await context.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => pageErrors.push(String(error)));
  await page.goto(`${baseUrl}?view=shorts`, { waitUntil: "networkidle" });
  await page.locator("#video-grid .video-card").first().waitFor({ state: "visible" });
  if (config.dark) await page.locator("#theme-toggle").click();
  if (config.english) await page.locator("#language-toggle").click();
  await page.waitForTimeout(250);

  const state = await page.evaluate(() => ({
    release: document.documentElement.dataset.release,
    language: document.documentElement.lang,
    direction: document.documentElement.dir,
    theme: document.documentElement.dataset.theme,
    resultCount: document.querySelector("#result-count")?.textContent?.trim(),
    cardCount: document.querySelectorAll("#video-grid .video-card").length,
    shortStat: document.querySelector('[data-stat="shorts"]')?.textContent?.trim(),
    cardText: [...document.querySelectorAll("#video-grid .video-card")].map((node) => node.textContent.trim()),
    horizontalOverflow: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
    titleVisible: Boolean(document.querySelector("#library-title")?.getClientRects().length),
  }));
  const expectedLanguage = config.english ? "en" : "he";
  const expectedDirection = config.english ? "ltr" : "rtl";
  const expectedTheme = config.dark ? "dark" : "light";
  const checks = {
    release_3_4_0: state.release === "3.4.0",
    language: state.language === expectedLanguage,
    direction: state.direction === expectedDirection,
    theme: state.theme === expectedTheme,
    result_count_153: /\b153\b/.test(state.resultCount || ""),
    initial_cards_rendered: state.cardCount > 0 && state.cardCount <= 153,
    shorts_stat_153: state.shortStat === "153",
    no_tractionator: !state.cardText.some((text) => /tractionator|gps tire/i.test(text)),
    no_horizontal_overflow: state.horizontalOverflow <= 1,
    title_visible: state.titleVisible,
    no_console_errors: consoleErrors.length === 0,
    no_page_errors: pageErrors.length === 0,
  };
  await page.screenshot({ path: path.join(SCREENSHOTS, `${config.name}.png`), fullPage: true });
  await context.close();
  return { name: config.name, viewport: config.viewport, state, checks, consoleErrors, pageErrors };
}

async function main() {
  fs.mkdirSync(SCREENSHOTS, { recursive: true });
  const port = await freePort();
  const baseUrl = `http://127.0.0.1:${port}/`;
  const server = spawn("python", ["tools/serve_local.py", "--host", "127.0.0.1", "--port", String(port)], {
    cwd: ROOT,
    stdio: "ignore",
    windowsHide: true,
  });
  let browser;
  try {
    await waitForServer(baseUrl);
    browser = await chromium.launch({ executablePath: chromePath(), headless: true });
    const configs = [
      { name: "desktop-he-light", viewport: { width: 1600, height: 1000 }, english: false, dark: false },
      { name: "desktop-en-dark", viewport: { width: 1600, height: 1000 }, english: true, dark: true },
      { name: "mobile-he-light", viewport: { width: 390, height: 844 }, english: false, dark: false },
      { name: "mobile-en-dark", viewport: { width: 390, height: 844 }, english: true, dark: true },
    ];
    const scenarios = [];
    for (const config of configs) scenarios.push(await scenario(browser, baseUrl, config));

    const routeContext = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: "he-IL" });
    const routePage = await routeContext.newPage();
    await routePage.goto(`${baseUrl}?view=shorts&category=route_navigation`, { waitUntil: "networkidle" });
    await routePage.waitForTimeout(300);
    const routeNavigation = await routePage.evaluate(() => ({
      resultCount: document.querySelector("#result-count")?.textContent?.trim(),
      cardCount: document.querySelectorAll("#video-grid .video-card").length,
      emptyVisible: !document.querySelector("#empty-state")?.hidden,
      categoryOptionExists: Boolean(document.querySelector('#filter-category option[value="route_navigation"]')),
      categoryStillInUrl: new URL(window.location.href).searchParams.get("category") === "route_navigation",
    }));
    await routeContext.close();

    const checks = Object.fromEntries(scenarios.flatMap((item) => Object.entries(item.checks).map(([key, value]) => [`${item.name}:${key}`, value])));
    checks["verified_navigation_category_visible"] = routeNavigation.categoryOptionExists && routeNavigation.categoryStillInUrl && routeNavigation.cardCount === 1;
    const report = {
      document_version: "1.2.0",
      product_version: "3.4.0",
      status: Object.values(checks).every(Boolean) ? "PASS" : "FAIL",
      real_browser: true,
      headless: true,
      base_url: baseUrl,
      checks,
      scenarios,
      route_navigation: routeNavigation,
    };
    fs.writeFileSync(path.join(OUT, "visual-qa.json"), `${JSON.stringify(report, null, 2)}\n`, "utf8");
    process.stdout.write(`${JSON.stringify({ status: report.status, checks_passed: Object.values(checks).filter(Boolean).length, checks_failed: Object.values(checks).filter((value) => !value).length }, null, 2)}\n`);
    process.exitCode = report.status === "PASS" ? 0 : 1;
  } finally {
    if (browser) await browser.close();
    server.kill();
  }
}

main().catch((error) => {
  process.stderr.write(`${error.stack || error}\n`);
  process.exitCode = 1;
});
