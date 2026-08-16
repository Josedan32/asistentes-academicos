export interface TokenOut {
  access_token: string;
  token_type: string;
  role: "student" | "coordination";
}

export interface MeOut {
  id: number;
  email: string;
  role: "student" | "coordination";
  first_name: string | null;
  last_name: string | null;
  document: string | null;
  program_id: number | null;
  program_code: string | null;
  program_name: string | null;
  current_semester: number | null;
}

export interface ProgramOut {
  id: number;
  code: string;
  name: string;
  semester_count: number;
  is_active: boolean;
  course_count: number;
}

export interface CourseOut {
  id: number;
  code: string;
  name: string;
  area: string;
  default_credits: number;
}

export interface SemesterCourseOut {
  id: number;
  code: string;
  name: string;
  area: string;
  credits: number;
  semester: number;
}

export interface EnrollmentOut {
  course_id: number;
  course_code: string;
  course_name: string;
  area: string;
  credits: number;
  period: string;
  times_taken: number;
}

export interface CurriculumBoardPrerequisiteOut {
  course_id: number;
  course_code: string;
  course_name: string;
}

export interface CurriculumBoardEntryOut {
  course_id: number;
  course_code: string;
  course_name: string;
  semester: number;
  credits: number;
  prerequisites: CurriculumBoardPrerequisiteOut[];
  shared_program_count: number;
}

export interface CoursePlacementOut {
  program_id: number;
  program_code: string;
  program_name: string;
  semester: number;
  credits: number;
}

export interface CourseWithUsageOut {
  id: number;
  code: string;
  name: string;
  area: string;
  default_credits: number;
  placements: CoursePlacementOut[];
}

export interface ToolCallOut {
  id: number;
  name: string;
  arguments: Record<string, unknown>;
  result: unknown;
  duration_ms: number;
  row_count: number;
  sequence: number;
}

export interface FeedbackOut {
  value: "up" | "down";
  comment: string | null;
}

export interface MessageOut {
  id: number;
  role: "user" | "assistant";
  content: string;
  mode: string | null;
  tool_calls: ToolCallOut[];
  feedback: FeedbackOut | null;
}

export interface ConversationSummaryOut {
  id: number;
  title: string;
  course_id: number | null;
  course_name: string | null;
  created_at: string;
}

export interface ConversationDetailOut {
  id: number;
  title: string;
  course_id: number | null;
  course_name: string | null;
  messages: MessageOut[];
}
