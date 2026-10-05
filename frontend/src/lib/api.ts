import {
  UserSession,
  InferenceResult,
  Doctor,
  Appointment,
  ScanRecord,
  FilterMetadata,
  RecommendationResponse
} from '../types';

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ||
  (typeof window !== 'undefined' ? '/api' : 'http://127.0.0.1:8000/api');


class ApiClient {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        ...(options?.headers || {}),
      },
    });

    if (!res.ok) {
      let errorMsg = `API Error: ${res.statusText}`;
      try {
        const errorJson = await res.json();
        if (errorJson.detail) {
          errorMsg = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
        }
      } catch (e) {
        // ignore parse error
      }
      throw new Error(errorMsg);
    }

    return res.json();
  }

  // --- 1. Auth & Users ---
  async login(username: string, password: string, role?: string): Promise<{ status: string; user: UserSession }> {
    return this.request<{ status: string; user: UserSession }>('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, role }),
    });
  }

  async register(data: {
    username: string;
    password: string;
    role: string;
    full_name: string;
    email: string;
    phone: string;
    city: string;
    extra_data?: any;
  }): Promise<{ status: string; message: string; user: UserSession }> {
    return this.request('/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  }

  async getDemoUsers(): Promise<{
    demo_accounts: UserSession[];
    custom_accounts: UserSession[];
    storage_mode: string;
  }> {
    return this.request('/auth/demo-users');
  }

  async getProfile(username: string): Promise<{ user: UserSession }> {
    return this.request(`/auth/me?username=${encodeURIComponent(username)}`);
  }

  async updateProfile(
    username: string,
    updates: Partial<UserSession>,
    new_password?: string
  ): Promise<{ status: string; message: string; user: UserSession }> {
    return this.request('/auth/profile', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, updates, new_password }),
    });
  }

  // --- 2. Inference & Samples ---
  async getSamples(): Promise<{ samples: Array<{ filename: string; directory: string; size_bytes: number }> }> {
    return this.request('/samples');
  }

  getSampleImageUrl(filename: string): string {
    return `${API_BASE}/samples/${encodeURIComponent(filename)}`;
  }

  async detectXray(formData: FormData): Promise<InferenceResult> {
    try {
      const res = await fetch(`${API_BASE}/inference/detect`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        let errorMsg = `Inference failed (HTTP ${res.status})`;
        try {
          const errJson = await res.json();
          if (errJson.detail) {
            errorMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
          }
        } catch (e) {}
        throw new Error(errorMsg);
      }

      return res.json();
    } catch (err: any) {
      if (err.message && !err.message.includes('Inference failed')) {
        throw new Error(`Connection to backend failed: ${err.message}. Please ensure the server on port 8000 is running.`);
      }
      throw err;
    }
  }

  // --- 3. Doctors & Recommendations ---
  async getDoctors(params: {
    query?: string;
    city?: string;
    specialization?: string;
    hospital?: string;
    min_rating?: number;
    max_fee?: number;
    availability?: string;
    page?: number;
    limit?: number;
  }): Promise<{
    total_count: number;
    page: number;
    limit: number;
    total_pages: number;
    doctors: Doctor[];
  }> {
    const query = new URLSearchParams();
    if (params.query) query.append('query', params.query);
    if (params.city && params.city !== 'All Cities') query.append('city', params.city);
    if (params.specialization && params.specialization !== 'All Specializations') query.append('specialization', params.specialization);
    if (params.hospital && params.hospital !== 'All Hospitals') query.append('hospital', params.hospital);
    if (params.min_rating) query.append('min_rating', params.min_rating.toString());
    if (params.max_fee) query.append('max_fee', params.max_fee.toString());
    if (params.availability) query.append('availability', params.availability);
    if (params.page) query.append('page', params.page.toString());
    if (params.limit) query.append('limit', params.limit.toString());

    return this.request(`/doctors?${query.toString()}`);
  }

  async registerSpecialist(data: any): Promise<{ status: string; message: string; doctor: any }> {
    return this.request('/doctors/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  }

  async matchRecommendations(data: {
    detected_findings: any[];
    city_filter?: string;
    hospital_filter?: string;
    availability_only?: boolean;
    max_fee?: number;
    top_k?: number;
  }): Promise<RecommendationResponse> {
    return this.request('/recommendations/match', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  }

  // --- 4. Appointments & Doctor Triage ---
  async createAppointment(data: {
    patient_username: string;
    patient_name: string;
    patient_phone: string;
    doctor_name: string;
    specialization?: string;
    hospital?: string;
    city?: string;
    clinical_indication?: string;
    appointment_slot?: string;
  }): Promise<{ status: string; appointment_id: string; message: string }> {
    return this.request('/appointments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  }

  async getAppointments(params: {
    patient_username?: string;
    doctor_name?: string;
    status_filter?: string;
  }): Promise<{ appointments: Appointment[]; count: number }> {
    const query = new URLSearchParams();
    if (params.patient_username) query.append('patient_username', params.patient_username);
    if (params.doctor_name) query.append('doctor_name', params.doctor_name);
    if (params.status_filter) query.append('status_filter', params.status_filter);

    return this.request(`/appointments?${query.toString()}`);
  }

  async confirmAppointment(
    appointment_id: string,
    data: { doctor_name: string; doctor_notes?: string; status: string }
  ): Promise<{ status: string; message: string }> {
    return this.request(`/appointments/${encodeURIComponent(appointment_id)}/confirm`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  }

  // --- 5. Scans & Reports ---
  async saveScan(data: {
    username: string;
    user_role: string;
    patient_name: string;
    patient_id: string;
    age: number;
    gender: string;
    city: string;
    findings_count: number;
    findings: any[];
    image_b64?: string;
  }): Promise<{ status: string; scan_id: string }> {
    return this.request('/scans', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  }

  async getScans(username?: string): Promise<{ scans: ScanRecord[]; count: number }> {
    const query = username ? `?username=${encodeURIComponent(username)}` : '';
    return this.request(`/scans${query}`);
  }

  async generateReportHtml(data: {
    report_id: string;
    patient_info: any;
    detection_results: any;
    referred_doctor?: any;
    annotated_img_b64?: string;
    doctor_notes?: string;
  }): Promise<string> {
    const res = await fetch(`${API_BASE}/reports/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return res.text();
  }

  // --- 6. Meta ---
  async getMetadata(): Promise<FilterMetadata> {
    return this.request('/meta/filters');
  }

  // --- 7. Clinical AI Chatbot ---
  async sendChatMessage(params: {
    message: string;
    history?: Array<{ role: string; content: string }>;
    context?: Record<string, any>;
  }): Promise<{ status: string; reply: string; timestamp: string }> {
    return this.request('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
  }
}

export const api = new ApiClient();

