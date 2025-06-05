import { get, post, del } from './http';
import { Tag } from './interface';

export async function getTags(): Promise<Tag[]> {
  return get<Tag[]>(`http://localhost:8080/tags`);
}

export async function createTag(name: string): Promise<Tag> {
  return post<Tag>(`http://localhost:8080/tags`, { name });
}

export async function deleteTag(tag_id: number): Promise<void> {
  return del<void>(`http://localhost:8080/tags/${tag_id}`);
}