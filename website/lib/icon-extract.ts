import sharp from "sharp";

// Sprite is 1024×1024 with FRONT on left half, BACK on right half.
// Crop the left 512×512 region (front sprite area) then resize to 40×40.
const FRONT_CROP = { left: 0, top: 0, width: 512, height: 1024 };
const ICON_SIZE = 40;

export async function extractIcon(spritePngBase64: string): Promise<string> {
  const buffer = Buffer.from(spritePngBase64, "base64");
  const iconBuffer = await sharp(buffer)
    .extract(FRONT_CROP)
    .resize(ICON_SIZE, ICON_SIZE, { kernel: "nearest" })
    .png()
    .toBuffer();
  return iconBuffer.toString("base64");
}
