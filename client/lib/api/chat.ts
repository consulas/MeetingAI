import { get, post } from "./http";
import { Setting, AudioConfig, ChatResponse } from "./interface";

export async function getSettings(): Promise<Setting[]> {
  return await get<Setting[]>("http://localhost:8080/settings");
}

export async function saveSetting(setting: Setting): Promise<Setting> {
  return await post<Setting, Setting>("http://localhost:8080/settings", setting);
}

export async function postChat(
  text: string,
  use_image: boolean,
  use_reasoning: boolean,
  questionType?: string
): Promise<ChatResponse> {
  return await post<ChatResponse, { conversation: string; question_type?: string; use_image: boolean; use_reasoning: boolean }>(
    "http://localhost:8080/chat",
    { conversation: text, question_type: questionType, use_image, use_reasoning }
  );
}

export async function getAudioConfigurationById(audioId: number): Promise<AudioConfig> {
  return await get<AudioConfig>(`http://localhost:8080/audio/${audioId}`);
}

export async function createAudioConfiguration(
  audioConfig: Partial<AudioConfig>
): Promise<AudioConfig> {
  return await post<AudioConfig, Partial<AudioConfig>>(
    "http://localhost:8080/audio",
    audioConfig
  );
}