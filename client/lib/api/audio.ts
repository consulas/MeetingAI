import { get, post } from "./http";
import { AudioConfig, AudioDevice } from "./interface";

export async function getAudioDevices(): Promise<Record<string, number>> {
  return await get<Record<string, number>>("http://localhost:8080/audio-devices");
}

export async function getAudioConfigurations(): Promise<AudioConfig[]> {
  return await get<AudioConfig[]>("http://localhost:8080/audio");
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