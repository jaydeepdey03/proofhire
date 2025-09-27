export interface User {
  id: string;
  email: string;
  name: string;
  type: "company" | "candidate";
  createdAt: string;
}

export interface Company extends User {
  type: "company";
  companyName: string;
  industry: string;
  size: string;
  description: string;
  website?: string;
  logo?: string;
}

export interface Candidate extends User {
  type: "candidate";
  title: string;
  experience: number;
  skills: string[];
  location: string;
  resume?: string;
  bio: string;
  education: string;
  phone?: string;
}

export interface Job {
  id: string;
  companyId: string;
  company?: Company;
  title: string;
  description: string;
  requirements: string[];
  skills: string[];
  location: string;
  type: "full-time" | "part-time" | "contract" | "internship" | "freelance";
  salary: {
    min: number;
    max: number;
    currency: string;
  };
  postedAt: string;
  deadline?: string;
  status: "active" | "inactive";
}

export interface Application {
  id: string;
  jobId: string;
  candidateId: string;
  job: Job;
  candidate: Candidate;
  status:
    | "pending"
    | "application_accepted"
    | "interview_scheduled"
    | "interview_completed"
    | "offer_given"
    | "offer_accepted"
    | "rejected";
  appliedAt: string;
  compatibilityScore?: number;
  aiApplied?: boolean;
  documents?: {
    type: "interview_proof" | "offer_letter";
    url: string;
    uploadedBy: "company" | "candidate";
    uploadedAt: string;
  }[];
  notes?: string;
}

export interface AISearchQuery {
  query: string;
  filters?: {
    experience?: number;
    skills?: string[];
    location?: string;
  };
}