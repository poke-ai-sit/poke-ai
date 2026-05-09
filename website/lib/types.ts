export interface GenerateRequest {
  prompt: string;
  referenceImageBase64?: string;
}

export interface GenerateResponse {
  spriteBase64: string;
  iconBase64: string;
}

export interface ApiError {
  error: string;
  code?: string;
}

export type GenerateState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; sprite: string; icon: string }
  | { status: "error"; message: string };
