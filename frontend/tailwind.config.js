/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        paper: "#fdfbf7",
        pencil: "#2d2d2d",
        erased: "#e5e0d8",
        marker: "#ff4d4d",
        pen: "#2d5da1",
        postit: "#fff9c4",
      },
      fontFamily: {
        heading: ["Kalam", "cursive"],
        body: ["Patrick Hand", "cursive"],
      },
      borderRadius: {
        wobbly: "255px 15px 225px 15px / 15px 225px 15px 255px",
        wobblyMd: "25px 225px 25px 225px / 225px 25px 225px 25px",
        wobblySm: "125px 10px 110px 10px / 10px 110px 10px 125px",
      },
      boxShadow: {
        sketch: "4px 4px 0px 0px #2d2d2d",
        sketchLg: "8px 8px 0px 0px #2d2d2d",
        sketchSm: "2px 2px 0px 0px #2d2d2d",
        sketchActive: "0px 0px 0px 0px #2d2d2d",
      }
    },
  },
  plugins: [],
}
