export interface AudioDevice {
  name: string
  channel: number
  n_channels: number
}

export interface AudioConfig {
  company: string
  audio_id: number
  devices: AudioDevice[]
}

export interface Tag {
  tag_id: number;
  name: string;
}

export interface Meeting {
  audio_id: number;
  meeting_id: number;
  title: string;
  status: string;
  start_time: string;
  end_time: string;
  audio_file: string | null;
  transcript: string;
  summary: string;
  tags: Tag[];
}

export interface Setting {
  key: string;
  value: string;
}

export interface ChatResponse {
  response: string;
  question_type: string;
}