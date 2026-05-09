import { NextRequest, NextResponse } from "next/server";
import { GenerateRequestSchema } from "@/lib/validation";
import { generateSprite, editSpriteWithReference } from "@/lib/openai-image";
import { extractIcon } from "@/lib/icon-extract";

export const runtime = "nodejs";
export const maxDuration = 90;

export async function POST(req: NextRequest) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const parsed = GenerateRequestSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: parsed.error.issues[0]?.message ?? "Invalid request" },
      { status: 400 },
    );
  }

  const { prompt, referenceImageBase64 } = parsed.data;

  try {
    const spriteBase64 = referenceImageBase64
      ? await editSpriteWithReference(prompt, referenceImageBase64)
      : await generateSprite(prompt);

    const iconBase64 = await extractIcon(spriteBase64);

    return NextResponse.json({ spriteBase64, iconBase64 });
  } catch (err: unknown) {
    if (err instanceof Error) {
      const msg = err.message.toLowerCase();
      if (msg.includes("rate limit") || msg.includes("429")) {
        return NextResponse.json(
          { error: "Rate limit reached. Please wait a moment and try again." },
          { status: 429 },
        );
      }
      if (msg.includes("openai") || msg.includes("api")) {
        return NextResponse.json(
          { error: "Sprite generation failed. Please try again." },
          { status: 502 },
        );
      }
    }
    return NextResponse.json(
      { error: "An unexpected error occurred. Please try again." },
      { status: 500 },
    );
  }
}
