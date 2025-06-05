import { get, post, del } from './http';
import { Meeting, Tag } from './interface';

export async function startMeeting(audio_id: number): Promise<Meeting> {
  return post<Meeting>(`http://localhost:8080/meetings/start`, { audio_id });
}

export async function stopMeeting(meeting_id: number): Promise<Meeting> {
  return post<Meeting>(`http://localhost:8080/meetings/${meeting_id}/stop`, {});
}

export async function renameMeeting(meeting_id: number, title: string): Promise<Meeting> {
  return post<Meeting>(`http://localhost:8080/meetings/${meeting_id}`, { title });
}

export async function getMeeting(meeting_id: number): Promise<Meeting> {
  return get<Meeting>(`http://localhost:8080/meetings/${meeting_id}`);
}

export async function getMeetings(page: number, tags: string[]): Promise<Meeting[]> {
  const queryParams = new URLSearchParams({ page: page.toString() });
  tags.forEach(tag => queryParams.append('tags', tag));
  return get<Meeting[]>(`http://localhost:8080/meetings?${queryParams.toString()}`);
}

export async function deleteMeeting(meeting_id: number): Promise<{ message: string }> {
  return del<{ message: string }>(`http://localhost:8080/meetings/${meeting_id}`);
}

export async function addTagToMeeting(meeting_id: number, name: string): Promise<Tag> {
  return post<Tag>(`http://localhost:8080/meetings/${meeting_id}/tags`, { name });
}

export async function deleteTagFromMeeting(meeting_id: number, tag_id: number): Promise<void> {
  return del<void>(`http://localhost:8080/meetings/${meeting_id}/tags/${tag_id}`);
}