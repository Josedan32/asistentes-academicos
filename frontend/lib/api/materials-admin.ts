import { apiFetch, getStoredToken } from "./client";

export interface CourseMaterialOut {
  id: number;
  course_id: number;
  filename: string;
}

export function listMaterials(courseId: number): Promise<CourseMaterialOut[]> {
  return apiFetch<CourseMaterialOut[]>(`/api/v1/admin/courses/${courseId}/materials`);
}

export async function uploadMaterial(courseId: number, file: File): Promise<CourseMaterialOut> {
  const token = getStoredToken();
  const formData = new FormData();
  formData.append("file", file);
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const response = await fetch(`${API_BASE_URL}/api/v1/admin/courses/${courseId}/materials`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    body: formData,
  });
  if (!response.ok) throw new Error(`Upload failed with status ${response.status}`);
  return response.json();
}

export function deleteMaterial(materialId: number): Promise<void> {
  return apiFetch<void>(`/api/v1/admin/materials/${materialId}`, { method: "DELETE" });
}
