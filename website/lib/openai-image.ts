import OpenAI from "openai";
import { SYSTEM_SPRITE_PROMPT, buildFinalPrompt } from "./prompts";

function getClient(): OpenAI {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) throw new Error("OPENAI_API_KEY is not set");
  return new OpenAI({ apiKey });
}

export async function generateSprite(userDescription: string): Promise<string> {
  const client = getClient();
  const result = await client.images.generate({
    model: "gpt-image-2",
    prompt: `${SYSTEM_SPRITE_PROMPT}\n\n${buildFinalPrompt(userDescription)}`,
    size: "1024x1024",
    quality: "high",
    n: 1,
  });
  const b64 = result.data?.[0]?.b64_json;
  if (!b64) throw new Error("No image data returned from OpenAI");
  return b64;
}

export async function editSpriteWithReference(
  userDescription: string,
  referenceImageBase64: string,
): Promise<string> {
  const client = getClient();
  const imageBuffer = Buffer.from(referenceImageBase64, "base64");
  const imageFile = new File([imageBuffer], "reference.png", {
    type: "image/png",
  });
  const result = await client.images.edit({
    model: "gpt-image-2",
    image: imageFile,
    prompt: `${SYSTEM_SPRITE_PROMPT}\n\n${buildFinalPrompt(userDescription)}`,
    size: "1024x1024",
    quality: "high",
    n: 1,
  });
  const b64 = result.data?.[0]?.b64_json;
  if (!b64) throw new Error("No image data returned from OpenAI");
  return b64;
}
