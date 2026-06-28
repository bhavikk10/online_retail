import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [
      { find: "lucide-react", replacement: path.resolve(__dirname, "src/utils/icons.jsx") },
      { find: "lodash/throttle", replacement: path.resolve(__dirname, "src/utils/lodash/throttle.js") },
      { find: /^lodash\/(.+)$/, replacement: path.resolve(__dirname, "src/utils/lodash/$1.js") },
      { find: /^@babel\/runtime\/helpers\/esm\/(.+)$/, replacement: path.resolve(__dirname, "node_modules/@babel/runtime/helpers/esm/$1.js") },
      { find: /^dom-helpers\/(.+)$/, replacement: path.resolve(__dirname, "node_modules/dom-helpers/esm/$1.js") },
    ],
  },
  optimizeDeps: {
    force: true,
  },
});
