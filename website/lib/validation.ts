import { z } from "zod";

export const GenerateRequestSchema = z.object({
  prompt: z
    .string()
    .min(3, "Describe your Pokémon (at least 3 characters)")
    .max(500, "Description too long (max 500 characters)"),
  referenceImageBase64: z.string().optional(),
});

export const GenerateResponseSchema = z.object({
  spriteBase64: z.string(),
  iconBase64: z.string(),
});

export type GenerateRequestInput = z.infer<typeof GenerateRequestSchema>;
