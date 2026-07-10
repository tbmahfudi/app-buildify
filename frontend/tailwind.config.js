/**
 * Tailwind build config — replaces the Play CDN (cdn.tailwindcss.com) with a static,
 * purged stylesheet (frontend/assets/css/app.build.css). The Play CDN is explicitly
 * "not for production" (FOUC, no purge, external runtime dep); this build emits a plain
 * CSS file any static server can serve, satisfying the static-deploy constraint.
 *
 * Build: from frontend/  ->  npm run build:css   (input assets/css/app.css)
 *
 * IMPORTANT — safelist: the SPA builds many class names dynamically in JS template
 * literals (e.g. `col-span-${n}`, `bg-${color}-500`, `grid-cols-${n}`). Tailwind's content
 * scanner only sees literal strings, so those must be safelisted or they get purged and
 * layouts/colors break. The patterns below cover the dynamic families found in the codebase.
 */
const COLORS = [
  'slate', 'gray', 'zinc', 'neutral', 'stone', 'red', 'orange', 'amber', 'yellow',
  'lime', 'green', 'emerald', 'teal', 'cyan', 'sky', 'blue', 'indigo', 'violet',
  'purple', 'fuchsia', 'pink', 'rose',
];

module.exports = {
  content: [
    './index.html',
    './portal/**/*.{html,js}',
    './assets/**/*.{html,js}',
    './components/**/*.{html,js}',
    // Module admin pages contribute Tailwind classes too (light-DOM, platform theme).
    '../modules/*/frontend/**/*.{html,js}',
  ],
  safelist: [
    // Grid spans / columns built as col-span-${n} / row-span-${n} / grid-cols-${n}
    { pattern: /^(col|row)-span-(1[0-2]|[1-9]|full)$/ },
    { pattern: /^grid-cols-(1[0-2]|[1-9])$/ },
    { pattern: /^gap-(0|1|2|3|4|5|6|8|10|12)$/ },
    // Color utilities built as (bg|text|border|from|to|ring|divide)-${color}-${shade}
    {
      pattern: new RegExp(`^(bg|text|border|from|to|ring|divide)-(${COLORS.join('|')})-(50|100|200|300|400|500|600|700|800|900)$`),
      variants: ['hover', 'focus', 'dark', 'group-hover'],
    },
    // Semantic fixed colors used dynamically (white/black/current/transparent)
    { pattern: /^(bg|text|border)-(white|black|transparent|current)$/ },
    // Sizing built as h-${n}/w-${n}/p-${n}/m-${n}
    { pattern: /^(h|w|p|m|px|py|mx|my|pt|pb|pl|pr|mt|mb|ml|mr)-(0|0\.5|1|1\.5|2|2\.5|3|3\.5|4|5|6|8|10|12|16|20|24|32|40|48|56|64|72|80|96|full|screen|auto)$/ },
  ],
  darkMode: 'class',
  theme: { extend: {} },
  plugins: [],
};
