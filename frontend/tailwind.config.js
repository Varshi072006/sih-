export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        forest: {
          950: "#071d19",
          900: "#0a2b24",
          800: "#123d34",
          700: "#1c5647",
          600: "#2e7a69",
        },
        teal: {
          500: "#3bb7a6",
          600: "#2a998c",
        },
        clay: "#ea7f48",
        gold: "#f4c96d",
        cream: "#f5f2eb",
        mist: "#edf6f1",
        ink: "#1b2a27",
      },
      boxShadow: {
        soft: "0 20px 50px rgba(12, 43, 36, 0.12)",
      },
      fontFamily: {
        serif: ['"Source Serif 4"', "Georgia", "serif"],
        sans: ['"Inter"', '"Segoe UI"', "sans-serif"],
      },
    },
  },
  plugins: [],
};
