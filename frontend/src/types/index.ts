export type UserRole = 'Patient' | 'Doctor' | 'Laboratory';

export interface UserSession {
  user_id?: string;
  username: string;
  role: UserRole;
  full_name: string;
  email: string;
  phone: string;
  city: string;
  age?: number;
  gender?: string;
  blood_group?: string;
  specialization?: string;
  hospital?: string;
  experience_years?: number;
  fees_inr?: number;
  rating?: number;
  availability?: string;
  disease_expertise?: string;
  license_no?: string;
  lead_radiologist?: string;
}

export interface Detection {
  detection_id: number;
  class_id: number;
  class_name: string;
  confidence: number;
  confidence_pct: string;
  bbox_pixels: [number, number, number, number];
  bbox_normalized: [number, number, number, number];
  location: string;
  severity: 'Critical' | 'High' | 'Moderate-High' | 'Moderate' | 'Low-Moderate' | 'Low';
  clinical_urgency: string;
}

export interface Doctor {
  doctor_name: string;
  specialization: string;
  disease_expertise: string;
  experience_years: number;
  rating: number;
  hospital: string;
  city: string;
  fees_inr: number;
  availability: string;
  is_registered?: boolean;
  is_exact_match?: boolean;
}

export interface RecommendationResponse {
  primary_specialty: string;
  clinical_urgency: string;
  clinical_summary: string;
  target_findings: string[];
  recommended_doctors: Doctor[];
  doctors: Doctor[];
}

export interface InferenceResult {
  model_version: string;
  source_image: string;
  image_dimensions: { width: number; height: number };
  findings_count: number;
  detections: Detection[];
  inference_time_ms: number;
  conf_threshold_used: number;
  iou_threshold_used: number;
  status: string;
  original_image_b64: string;
  annotated_image_b64: string;
  recommendations: RecommendationResponse;
}

export interface Appointment {
  appointment_id: string;
  patient_username: string;
  patient_name: string;
  patient_phone: string;
  doctor_name: string;
  specialization?: string;
  hospital?: string;
  city?: string;
  clinical_indication?: string;
  appointment_slot?: string;
  status: 'Pending' | 'Confirmed' | 'Declined';
  doctor_notes?: string;
  doctor_confirmed_at?: string;
  created_at: string;
}

export interface ScanRecord {
  scan_id: string;
  username: string;
  user_role: string;
  lab_name?: string;
  patient_name: string;
  patient_id: string;
  age: number;
  gender: string;
  city: string;
  findings_count: number;
  findings: Detection[];
  image_b64?: string;
  timestamp: string;
}

export interface FilterMetadata {
  cities: string[];
  specializations: string[];
  hospitals: string[];
  target_classes: string[];
  severity_mapping: Record<string, { severity: string; urgency: string }>;
  storage_mode: string;
  total_doctors: number;
}
