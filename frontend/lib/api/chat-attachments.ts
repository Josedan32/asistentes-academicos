import { getStoredToken } from "./client";

export interface ChatAttachmentOut {
  filename: string;
  text: string;
}

/** Manual fetch instead of apiFetch: the latter forces a JSON Content-Type, which breaks
 * multipart/form-data uploads — same reasoning as uploadMaterial in materials-admin.ts. */
export async function uploadChatAttachment(file: File): Promise<ChatAttachmentOut> {
  const token = getStoredToken();
  const formData = new FormData();
  formData.append("file", file);
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const response = await fetch(`${API_BASE_URL}/api/v1/chat/attachments`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    body: formData,
  });
  if (!response.ok) throw new Error(`Upload failed with status ${response.status}`);
  return response.json();
}
