import { apiFetch } from "./client";
import type { CourseOut, CourseWithUsageOut } from "../types";

export function listCourses(): Promise<CourseWithUsageOut[]> {
  return apiFetch<CourseWithUsageOut[]>("/api/v1/admin/courses");
}

export interface CoursePayload {
  code: string;
  name: string;
  area: string;
  default_credits: number;
  description?: string;
}

export function createCourse(payload: CoursePayload): Promise<CourseOut> {
  return apiFetch<CourseOut>("/api/v1/admin/courses", {
    method: "POST", body: JSON.stringify(payload),
  });
}

export function updateCourse(id: number, payload: CoursePayload): Promise<CourseOut> {
  return apiFetch<CourseOut>(`/api/v1/admin/courses/${id}`, {
    method: "PATCH", body: JSON.stringify(payload),
  });
}
