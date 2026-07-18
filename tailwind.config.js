/**
 * Tema Tailwind de VATISHE, derivado del design system "VATISHE Core" de Stitch.
 * Estilo: Minimalismo Corporativo (navy + superficies claras, Hanken Grotesk / Inter).
 */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./apps/**/templates/**/*.html",
    "./apps/**/*.py",
    "./static/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#1a1a2e", // navy corporativo (primary-container de Stitch)
          fg: "#ffffff",
          soft: "#83829b",
          fixed: "#e2e0fc",
        },
        // Naranja de acento: EXCLUSIVO para llamadas a la acción (CTA), "Pagar",
        // indicadores de progreso. Alto contraste contra el navy estructural.
        accent: {
          DEFAULT: "#ff8c00",
          fg: "#ffffff",
        },
        secondary: {
          DEFAULT: "#5d5f5f",
          container: "#dfe0e0",
          fg: "#ffffff",
        },
        tertiary: {
          DEFAULT: "#695d3c",
          container: "#b9aa83",
        },
        surface: {
          DEFAULT: "#fcf8fa",
          dim: "#ddd9db",
          lowest: "#ffffff",
          low: "#f6f2f4",
          container: "#f1edef",
          high: "#ebe7e9",
          highest: "#e5e1e3",
        },
        ink: {
          DEFAULT: "#1c1b1d", // on-surface
          variant: "#47464c", // on-surface-variant
        },
        outline: {
          DEFAULT: "#78767d",
          variant: "#c8c5cd",
        },
        // Colores semánticos (chips de estado: pagado / pendiente / vencido).
        success: { DEFAULT: "#2e7d32", container: "#c8e6c9", fg: "#0b3d0f" },
        warning: { DEFAULT: "#b26a00", container: "#ffe0b2", fg: "#4a2c00" },
        danger: { DEFAULT: "#ba1a1a", container: "#ffdad6", fg: "#93000a" },
      },
      fontFamily: {
        display: ['"Hanken Grotesk"', "system-ui", "sans-serif"],
        sans: ['"Inter"', "system-ui", "sans-serif"],
      },
      borderRadius: {
        DEFAULT: "0.5rem",
        md: "0.75rem",
        lg: "1rem",
        xl: "1.5rem",
      },
      boxShadow: {
        card: "0px 4px 12px rgba(26, 26, 46, 0.05)",
        "card-hover": "0px 6px 18px rgba(26, 26, 46, 0.10)",
      },
      maxWidth: {
        container: "1200px",
        app: "480px", // ancho de lectura móvil (PWA)
      },
    },
  },
  plugins: [],
};
