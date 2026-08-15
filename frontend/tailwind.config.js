/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Palette "sala di proiezione": non nero puro, blu-antracite profondo
        reel: {
          bg: "#0C0F14",
          surface: "#14181F",
          surfaceHover: "#1B212B",
          border: "#262C36",
        },
        paper: "#EDEAE2",       // testo primario, bianco caldo da manifesto
        muted: "#8B93A1",       // testo secondario
        marquee: "#D8A945",     // oro insegna cinema: accento, usato con parsimonia
        velvet: "#8C2F39",      // rosso sipario: badge qualita/genere
      },
      fontFamily: {
        display: ["var(--font-fraunces)", "serif"],
        sans: ["var(--font-inter)", "sans-serif"],
        mono: ["var(--font-plex-mono)", "monospace"],
      },
    },
  },
  plugins: [],
};
