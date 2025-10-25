import fs from "fs";

// Paths to CodeRabbit outputs
const localPath = "/tmp/coderabbit_local.json";
const mainPath = "/tmp/coderabbit_main.json";

// Read files safely
function readIfExists(path) {
  if (fs.existsSync(path)) {
    return fs.readFileSync(path, "utf-8");
  } else {
    console.warn(`Missing: ${path}`);
    return "";
  }
}

const localData = readIfExists(localPath);
const mainData = readIfExists(mainPath);

// Merge and normalize
const combinedReview = `
### MAIN Branch Review
${mainData}

### FEATURE Branch Review
${localData}
`;

// Save to a new file if you want to feed it elsewhere
fs.writeFileSync("./context/review_context.txt", combinedReview);
console.log("✅ Saved combined review to context/review_context.txt");