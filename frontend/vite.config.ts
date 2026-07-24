import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: "/ai-labor-observatory/",
  plugins: [react()],
  server: {
    port: 5173,
  },
});
