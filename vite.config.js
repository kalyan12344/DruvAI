import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  server: {
    port: 5176, // Forces port 5176
    strictPort: true, // Fails if port is occupied
  },
  plugins: [react()],
});
