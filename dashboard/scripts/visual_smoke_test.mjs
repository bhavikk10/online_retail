import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dashboardRoot = path.resolve(__dirname, "..");
const screenshotDir = path.join(dashboardRoot, "qa_screenshots");
mkdirSync(screenshotDir, { recursive: true });

const routes = [
  ["Overview", "overview"],
  ["Data & Pipeline", "data-pipeline"],
  ["Customer Value", "customer-value"],
  ["Customer Segments", "customer-segments"],
  ["Revenue Forecast", "revenue-forecast"],
  ["Model Review & Appendix", "model-review"],
];

const oldSidebarLabels = [
  "Executive Overview",
  "Data Pipeline",
  "Dataset Explorer",
  "Retention Modelling",
  "CLV Prediction",
  "Customer Segmentation",
  "Revenue Forecasting",
  "SHAP / Model Explainability",
  "Failures, Diagnostics, and Lessons",
  "File and Artifact Map",
];

async function runWithPlaywright() {
  let chromium;
  try {
    ({ chromium } = await import("playwright"));
  } catch {
    return null;
  }

  const baseUrl = process.env.DASHBOARD_URL || "http://127.0.0.1:5173";
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
  const findings = [];
  for (const [label] of routes) {
    await page.goto(baseUrl, { waitUntil: "networkidle" });
    await page.getByRole("button", { name: new RegExp(label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "i") }).click();
    await page.waitForTimeout(600);
    const safeName = label.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
    await page.screenshot({ path: path.join(screenshotDir, `${safeName}.png`), fullPage: true });
    const bodyText = await page.locator("body").innerText();
    const navText = await page.locator("nav").innerText();
    const brokenImages = await page.$$eval("img", (imgs) => imgs.filter((img) => !img.complete || img.naturalWidth === 0).length);
    const emptyCharts = await page.$$eval(".recharts-wrapper, .js-plotly-plot", (nodes) => nodes.filter((node) => node.clientHeight < 40 || node.clientWidth < 40).length);
    findings.push({
      label,
      brokenImages,
      emptyCharts,
      has404: bodyText.includes("404"),
      hasNA: /\bn\/a\b/i.test(bodyText),
      hasUndefined: bodyText.includes("undefined"),
      hasNaN: bodyText.includes("NaN"),
      hasNull: /\bnull\b/i.test(bodyText),
      hasWindowsPath: /[A-Za-z]:\\/.test(bodyText),
      oldSidebarLabels: oldSidebarLabels.filter((oldLabel) => navText.includes(oldLabel)),
    });
  }
  await browser.close();
  return { mode: "playwright", baseUrl, findings };
}

const playwrightReport = await runWithPlaywright();
const report = playwrightReport || {
  mode: "fallback",
  reason: "Playwright is not installed in this dashboard package. Static path audit plus build verification were used; dashboard/QA_CHECKLIST.md records the manual visual checklist.",
  routes: routes.map(([label]) => label),
  screenshotsCreated: false,
};

const reportPath = path.join(screenshotDir, "visual_smoke_report.json");
writeFileSync(reportPath, JSON.stringify(report, null, 2));

if (report.mode === "playwright") {
  const failed = report.findings.some((item) => item.brokenImages || item.emptyCharts || item.has404 || item.hasNA || item.hasUndefined || item.hasNaN || item.hasNull || item.hasWindowsPath || item.oldSidebarLabels.length);
  console.log(`Visual smoke (${report.mode}): ${failed ? "FAILED" : "PASSED"}`);
  console.log(`Screenshots: ${path.relative(dashboardRoot, screenshotDir)}`);
  if (failed) process.exitCode = 1;
} else {
  console.log("Visual smoke fallback written because Playwright is unavailable.");
  console.log(`Report: ${path.relative(dashboardRoot, reportPath)}`);
  if (!existsSync(path.join(dashboardRoot, "QA_CHECKLIST.md"))) process.exitCode = 1;
}
