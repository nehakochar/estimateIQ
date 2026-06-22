export interface SubFeatureItem {
  id: string;
  sub_feature_name: string;
  description: string;
  frontend_hours: number;
  backend_hours: number;
  mobile_hours: number;
  complexity: 'Low' | 'Medium' | 'High';
  assumptions?: string | null;
}

export interface RequirementEstimateGroup {
  requirement_id: string;
  req_id: string;
  name: string;
  req_type: string;
  description: string;
  sub_features: SubFeatureItem[];
  subtotal_frontend: number;
  subtotal_backend: number;
  subtotal_mobile: number;
  subtotal_total: number;
}

export interface ProjectEstimatesResponse {
  project_id: string;
  estimation_status: 'not_started' | 'generating' | 'completed' | 'failed';
  total_frontend_hours: number;
  total_backend_hours: number;
  total_mobile_hours: number;
  grand_total_hours: number;
  requirements: RequirementEstimateGroup[];
}
