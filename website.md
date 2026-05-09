# Sprint-004: Pokémon FireRed Sprite Generator Website

**Owner:** Desmond Chye Zhi Hao (+ Shaun Liew helping)
**Branch:** `feat/004-pokemon-creator`
**Hackathon:** AI Engineer Hackathon, Singapore, May 9 2026

---

## What We're Building

A standalone Next.js 14 website that lets users:
1. Type a text description of a custom Pokémon concept
2. Optionally upload a reference image
3. Click **Generate** → calls OpenAI `gpt-image-2` API server-side
4. Displays the 64×64 pixel sprite sheet (FRONT + BACK side by side)
5. Displays a 40×40 party/Pokédex icon
6. Download buttons for both assets
7. UI styled to match Pokémon FireRed (Press Start 2P font, navy/red/cream palette, chunky pixel borders)

---

## Tech Stack

| Layer | Choice |
|---|---|
| Framework | Next.js 14 (App Router) |
| Styling | TailwindCSS + CSS variables |
| Language | TypeScript |
| Image API | OpenAI `gpt-image-2` |
| Icon crop | `sharp` (server-side nearest-neighbor resize) |
| Validation | Zod |
| Font | Press Start 2P (Google Fonts) |

---

## gpt-image-2 API Reference

### Model Details
- **Model name:** `gpt-image-2`
- **Latest snapshot:** `gpt-image-2-2026-04-21`
- **Endpoints:**
  - Generate: `POST /v1/images/generations`
  - Edit (with reference image): `POST /v1/images/edits`

### Key Parameters

| Parameter | Value for this project | Notes |
|---|---|---|
| `model` | `"gpt-image-2"` | |
| `size` | `"1024x1024"` | Both edges must be multiples of 16; ratio ≤ 3:1; total pixels 655K–8.3M |
| `quality` | `"high"` | Options: `low`, `medium`, `high`, `auto` |
| `output_format` | `"png"` | Also supports `jpeg`, `webp` |
| `background` | `"opaque"` | `transparent` not supported on gpt-image-2; white bg handled via system prompt |
| `n` | `1` | |
| Response field | `result.data[0].b64_json` | Base64-encoded PNG |

> **Icon note:** gpt-image-2 minimum size is ~810×810 (655,360 pixel minimum). Cannot generate 40×40 directly — use server-side `sharp` crop + resize instead.

### Generate (text only) — Node.js
```ts
const result = await openai.images.generate({
  model: "gpt-image-2",
  prompt: fullPrompt,       // system prompt + user description combined
  size: "1024x1024",
  quality: "high",
  output_format: "png",
  background: "opaque",
  n: 1,
});
const spriteBase64 = result.data[0].b64_json;
```

### Edit (with reference image) — Node.js
```ts
// Convert incoming base64 string → File object for the SDK
const imageBuffer = Buffer.from(referenceImageBase64, "base64");
const imageFile = new File([imageBuffer], "reference.png", { type: "image/png" });

const result = await openai.images.edit({
  model: "gpt-image-2",
  image: imageFile,
  prompt: fullPrompt,
  size: "1024x1024",
  quality: "high",
  output_format: "png",
  n: 1,
});
const spriteBase64 = result.data[0].b64_json;
```

---

## Prompts

### System Prompt (proven by teammate in ChatGPT)
```
You are a Pokemon sprite artist specializing in Game Boy Advance FireRed style. Generate a Pokemon sprite with these STRICT requirements:
- Exactly 64x64 pixels
- Pixel art style with HARD edges only, absolutely NO anti-aliasing, NO gradients, NO soft shadows
- Maximum 15 colors total (not counting white background)
- Pure white background (#FFFFFF) - this will become transparent in-game
- Bold black outlines around the Pokemon
- Chunky, simple shapes that read clearly at small size
- Flat color fills with at most 2-3 shades per color region
- Style reference: Gen 3 Pokemon sprites (Ruby/Sapphire/FireRed era)
Generate TWO images side by side in one image:
- LEFT: front view (facing slightly right, as if looking at player)
- RIGHT: back view (rear of the Pokemon, as if walking away)
Label them "FRONT" and "BACK" below each sprite.
```

### User Prompt Format
Prefix the user's input with:
```
The Pokemon is: <user description here>
```

### Example Prompts (known-good from teammate testing)
```
The Pokemon is: a small cute rusty old car, round headlights as eyes, happy expression, compact kei-car body style

The Pokemon is: a sleek red Ferrari sports car Pokemon, aggressive headlights as eyes, low to the ground, intimidating expression, exhaust flames coming from the back

The Pokemon is: a Pokemon based on Michael Jackson's Smooth Criminal era - white fedora hat, white suit with black armband, doing the iconic 45-degree gravity-defying lean pose, one hand pointing forward, sparkly glove on one hand, humanoid but with cute Pokemon proportions, confident smirking expression
```

---

## Directory Structure

```
website/                                  ← standalone Next.js app (new dir in monorepo)
  .env.local                              ← OPENAI_API_KEY (gitignored — NEVER commit)
  .env.example                            ← committed template (key value blank)
  .gitignore                              ← node_modules, .next, .env*
  package.json
  tsconfig.json
  next.config.mjs
  tailwind.config.ts
  postcss.config.mjs
  app/
    layout.tsx                            ← root layout, loads Press Start 2P font
    page.tsx                              ← server component, renders HomeClient
    globals.css                           ← Tailwind + FireRed CSS variables
    api/
      generate-sprite/
        route.ts                          ← POST handler → OpenAI gpt-image-2
  components/
    HomeClient.tsx                        ← client component, useReducer state machine
    SpriteGeneratorForm.tsx               ← prompt textarea + image upload + submit button
    SpritePreview.tsx                     ← 64×64 sprite display (pixelated upscale)
    IconPreview.tsx                       ← 40×40 icon display (party slot style)
    LoadingDialog.tsx                     ← FireRed "..." animated battle dialog
    ErrorDialog.tsx                       ← red-bordered error panel + retry button
    FireRedPanel.tsx                      ← reusable bordered panel (default/red/dialog)
    ImageUpload.tsx                       ← drag-drop + file picker + client resize
  lib/
    openai-image.ts                       ← server-only gpt-image-2 wrapper (lazy init)
    prompts.ts                            ← SYSTEM_SPRITE_PROMPT + buildFinalPrompt()
    validation.ts                         ← Zod schemas for request/response
    icon-extract.ts                       ← sharp: crop front half + resize to 40×40
    types.ts                              ← shared TypeScript types
  public/
    placeholder-sprite.png               ← shown before first generation
    favicon.ico
  README.md                              ← run instructions for teammates and judges
```

---

## FireRed UI Theme

### CSS Variables (`app/globals.css`)
```css
:root {
  --fr-navy:   #18204b;   /* background panels */
  --fr-red:    #b81818;   /* accents, buttons */
  --fr-cream:  #f8f8e8;   /* text areas, content bg */
  --fr-border: #181818;   /* thick black outlines */
  --fr-shadow: #585858;   /* inset shadow side */
  --fr-white:  #ffffff;   /* highlight side */
}
```

### Font
```ts
// app/layout.tsx
import { Press_Start_2P } from "next/font/google";
const pixelFont = Press_Start_2P({ weight: "400", subsets: ["latin"] });
```

### FireRedPanel component
Thick black outer border + 2px inset highlight (white top-left, dark gray bottom-right) + cream background. Three variants: `default`, `red`, `dialog`.

### Sprite display
```css
image-rendering: pixelated;   /* CSS — no browser smoothing */
image-rendering: crisp-edges; /* Firefox fallback */
```
Render at 4× scale: 64×64 sprite → displayed at 256×256 (front+back together: 512×256).

---

## API Route (`app/api/generate-sprite/route.ts`)

```ts
export const runtime = "nodejs";   // required for sharp
export const maxDuration = 90;     // gpt-image-2 can take up to 2 min

// POST body shape (validated by Zod)
// { prompt: string, referenceImageBase64?: string }

// Response shape
// { spriteBase64: string, iconBase64: string }

// Error responses
// 400 — validation error (missing/invalid prompt)
// 429 — OpenAI rate limit
// 502 — OpenAI API error
// 500 — unexpected server error
// NEVER include OPENAI_API_KEY in any error message
```

---

## Icon Extraction (`lib/icon-extract.ts`)

```ts
import sharp from "sharp";

export async function extractIcon(spritePngBase64: string): Promise<string> {
  const buffer = Buffer.from(spritePngBase64, "base64");
  // Sprite is 1024×1024 with FRONT on left half, BACK on right half
  // Crop left 512×1024, then find the Pokemon in the center and resize to 40×40
  const iconBuffer = await sharp(buffer)
    .extract({ left: 0, top: 0, width: 512, height: 1024 })  // front half
    .resize(40, 40, { kernel: "nearest" })                    // pixelated resize
    .png()
    .toBuffer();
  return iconBuffer.toString("base64");
}
```

> **Note:** Crop coordinates are tunable constants — verify visually on first generation. If the model places the label text differently, adjust the `extract` region. Phase 5 fallback: second API call for a dedicated icon if cropping looks bad.

---

## Implementation Phases

### Phase 1 — Scaffolding
1. `npx create-next-app@14 website --typescript --tailwind --app --eslint` (from monorepo root)
2. `npm i openai zod sharp` + `npm i -D @types/node`
3. Set up `.env.local` with `OPENAI_API_KEY`, create `.env.example`, update `.gitignore`
4. Add FireRed CSS variables + Press Start 2P font to `globals.css` / `layout.tsx`
5. Build `FireRedPanel` base component

### Phase 2 — Server API (test with curl before touching UI)
6. Define `types.ts` and Zod schemas in `validation.ts`
7. Write `prompts.ts` — `SYSTEM_SPRITE_PROMPT` constant + `buildFinalPrompt(userPrompt)`
8. Write `openai-image.ts` — `generateSprite()` and `editSpriteWithReference()` (lazy OpenAI client)
9. Write `icon-extract.ts` — `extractIcon()` using sharp
10. Write the API route `app/api/generate-sprite/route.ts`
11. **Smoke test:** `curl -X POST localhost:3000/api/generate-sprite -H "Content-Type: application/json" -d '{"prompt":"a small cute rusty old car..."}'` → decode base64 → open PNG

### Phase 3 — UI Core
12. `SpriteGeneratorForm` — textarea, ImageUpload, submit button, disabled states
13. `ImageUpload` — drag/drop + file picker, client-side canvas resize to ≤1 MB, preview + remove
14. `SpritePreview` — pixelated upscale, download button
15. `IconPreview` — 40×40 party slot, download button
16. `HomeClient` + `page.tsx` — `useReducer` state: `idle → loading → success/error`

### Phase 4 — States + Polish
17. `LoadingDialog` — animated FireRed "..." text, CSS keyframes
18. `ErrorDialog` — red panel, friendly error messages, retry button
19. Wire fetch with `AbortController` 90s timeout + HTTP status → error message mapping
20. Download helpers (`downloadBase64Png`)

### Phase 5 — Optional (cut if time-pressed)
21. Example prompt chips ("Rusty Car", "Ferrari", "Smooth Criminal") that fill the textarea
22. Sound effect on generation complete (muted by default)
23. Backup second API call for icon if sharp crop quality is poor

### Phase 6 — Branch + Handoff
24. `git checkout -b feat/004-pokemon-creator` → commit (verify `.env.local` is NOT staged)
25. Write `README.md` with run instructions

---

## Risks & Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| `.env.local` accidentally committed | **HIGH** | Always run `git status` before commit; `.gitignore` covers `.env*`; never `git add .` blindly |
| OpenAI API key leaks to browser | **HIGH** | ALL OpenAI calls in `app/api/` route only — never import `openai-image.ts` in client components |
| `sharp` install fails on Apple Silicon | MEDIUM | `npm i --include=optional sharp`; fallback: `@napi-rs/canvas` |
| Icon crop coordinates wrong | MEDIUM | Make crop region tunable constants; check visually on first generation |
| Reference image upload exceeds Next.js body limit (1 MB default) | MEDIUM | Client-side canvas resize before upload; or configure `bodyParser` limit in `next.config.mjs` |
| OpenAI rate limit / quota during demo | MEDIUM | Pre-generate 3 images before stage time; cache last results in `localStorage` |
| Slow generation (up to 2 min) frustrating judges | MEDIUM | `LoadingDialog` with animated indicator; use `quality: "medium"` for speed during demo if needed |

---

## Success Criteria

- [ ] "rusty old car" prompt → 64×64 sprite appears within 90 s
- [ ] Reference image upload also generates a valid sprite
- [ ] 40×40 icon shown alongside sprite
- [ ] Download buttons produce valid PNG files
- [ ] `OPENAI_API_KEY` never appears in browser network tab
- [ ] `git status` after commit shows no `.env*` files staged
- [ ] UI uses Press Start 2P font, navy/red/cream palette, chunky pixel borders
- [ ] Error states render gracefully
- [ ] `npm run build` passes with zero TypeScript errors
- [ ] README documents how to run on a fresh machine

---

## Environment Setup (for anyone running this fresh)

```bash
# 1. Install dependencies
cd website
npm install

# 2. Set up API key
cp .env.example .env.local
# Edit .env.local and set: OPENAI_API_KEY=sk-...

# 3. Run dev server
npm run dev
# → http://localhost:3001  (or 3000 if bridge isn't running)

# 4. Build check
npm run build
```

---

## Notes

- The bridge FastAPI server runs on `localhost:8000` — run the Next.js dev server on a different port (`PORT=3001 npm run dev`) to avoid conflicts
- The `OPENAI_API_KEY` is the same key used by the FastAPI bridge — copy the value from `bridge/.env`
- Do NOT symlink `.env.local` to `bridge/.env` — they are separate files with different formats
- The generated sprite has a white background (`#FFFFFF`) which becomes transparent when loaded into the FireRed ROM (the game engine treats white as transparent)
- `image-rendering: pixelated` is the CSS property that gives the upscaled sprite its chunky look — do not use `image-rendering: auto` or the browser will blur it
