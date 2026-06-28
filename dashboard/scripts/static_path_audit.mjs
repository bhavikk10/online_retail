import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dashboardRoot = path.resolve(__dirname, "..");
const srcRoot = path.join(dashboardRoot, "src");
const publicRoot = path.join(dashboardRoot, "public");
const reportPath = path.join(dashboardRoot, "qa_screenshots", "static_path_audit.json");
mkdirSync(path.dirname(reportPath), { recursive: true });

function walk(dir, files = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full, files);
    else if (/\.(jsx?|tsx?)$/.test(entry.name)) files.push(full);
  }
  return files;
}

function classify(publicPath) {
  if (publicPath.includes("/shap_plots/") || publicPath.includes("/shap_outputs/")) return "optional";
  return "required";
}

function toPublicFile(publicPath) {
  return path.join(publicRoot, publicPath.replace(/^\//, "").replace(/\//g, path.sep));
}

const files = walk(srcRoot);
const references = [];
const publicPathPattern = /["'`]((?:\/)(?:final_outputs|raw_outputs|generated|assets)\/[^"'`\s)]+)["'`]/g;
const absoluteWindowsPattern = /[A-Za-z]:\\/g;

for (const file of files) {
  const source = readFileSync(file, "utf8");
  let match;
  while ((match = publicPathPattern.exec(source))) {
    const publicPath = match[1];
    if (publicPath.includes("${")) continue;
    const target = toPublicFile(publicPath);
    references.push({
      file: path.relative(dashboardRoot, file).replace(/\\/g, "/"),
      publicPath,
      status: existsSync(target) ? "valid" : "missing",
      requirement: classify(publicPath),
      bytes: existsSync(target) ? statSync(target).size : 0,
    });
  }
  while ((match = absoluteWindowsPattern.exec(source))) {
    references.push({
      file: path.relative(dashboardRoot, file).replace(/\\/g, "/"),
      publicPath: match[0],
      status: "invalid",
      requirement: "required",
      reason: "Absolute Windows path found in React source.",
    });
  }
}

const valid = references.filter((item) => item.status === "valid");
const broken = references.filter((item) => item.status !== "valid" && item.requirement === "required");
const optionalMissing = references.filter((item) => item.status !== "valid" && item.requirement === "optional");
const report = {
  checkedAt: new Date().toISOString(),
  sourceRoot: "dashboard/src",
  validCount: valid.length,
  brokenCount: broken.length,
  optionalMissingCount: optionalMissing.length,
  valid,
  broken,
  optionalMissing,
};

writeFileSync(reportPath, JSON.stringify(report, null, 2));
console.log(`Static path audit: ${valid.length} valid, ${broken.length} broken required, ${optionalMissing.length} optional missing.`);
console.log(`Report: ${path.relative(dashboardRoot, reportPath)}`);
if (broken.length) {
  console.error(JSON.stringify(broken, null, 2));
  process.exitCode = 1;
}
