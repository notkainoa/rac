import { defineConfig, fontProviders } from "astro/config";
import react from "@astrojs/react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  site: "https://racbrowser.com",
  output: "static",
  // The whole stylesheet is small, so inline it and save a blocking request.
  build: { inlineStylesheets: "always" },
  integrations: [react()],
  vite: { plugins: [tailwindcss()] },
  // Font files are bundled from npm and served by the site itself. Nothing
  // is fetched from a font service, and Astro generates metric-matched
  // fallbacks so swapping in the real face doesn't shift the layout.
  fonts: [
    {
      provider: fontProviders.local(),
      name: "Inter",
      cssVariable: "--font-inter",
      fallbacks: ["system-ui", "sans-serif"],
      options: {
        variants: [
          {
            // Inter with its optical size axis, so headlines get the display cut.
            src: ["@fontsource-variable/inter/files/inter-latin-opsz-normal.woff2"],
            weight: "100 900",
            style: "normal",
          },
        ],
      },
    },
  ],
});
