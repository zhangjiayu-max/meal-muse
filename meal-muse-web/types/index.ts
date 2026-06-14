export interface User {
  id: string;
  phone: string | null;
  nickname: string;
  avatar_url: string | null;
  gender: string | null;
  age: number | null;
  birthday: string | null;
  height_cm: number | null;
  current_weight: number | null;
  target_weight: number | null;
  activity_level: string;
  preferences: Record<string, unknown> | null;
  daily_calorie_target: number | null;
  status: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface UserProfile {
  taste_preference: string;
  diet_type: string;
  cuisine_preference: string[] | null;
  disliked_foods: string[] | null;
  cooking_method: string;
  cooking_facility: string;
  meal_pattern: string;
  sleep_pattern: string;
  care_targets: string[] | null;
  budget_level: string;
  meal_prep_time: string;
  water_intake_goal: number | null;
}

export interface HealthGoal {
  id: string;
  goal_type: string;
  target_weight: number | null;
  target_date: string | null;
  daily_calorie_target: number | null;
  macro_targets: Record<string, number> | null;
  special_notes: string | null;
  status: string;
}

export interface AllergyTag {
  id: string;
  allergen: string;
  custom_name: string | null;
  reaction_level: string;
}

export interface HealthCondition {
  id: string;
  condition_type: string;
  severity: string;
  diagnosed_date: string | null;
}

export interface FullProfile {
  user: User;
  profile: UserProfile | null;
  health_goals: HealthGoal[];
  allergies: AllergyTag[];
  health_conditions: HealthCondition[];
}

export interface FoodItem {
  name: string;
  amount: string;
  calories: number;
  protein: number;
  fat: number;
  carbs: number;
}

export interface DietRecord {
  id: string;
  meal_type: "breakfast" | "lunch" | "dinner" | "snack";
  food_text: string;
  parsed_foods: FoodItem[] | null;
  total_calories: number;
  total_protein: number;
  total_fat: number;
  total_carbs: number;
  total_fiber: number;
  ai_analysis: string | null;
  recorded_at: string;
  source: string;
  created_at: string;
}

export interface DailyDietSummary {
  date: string;
  total_calories: number;
  total_protein: number;
  total_fat: number;
  total_carbs: number;
  total_fiber: number;
  meal_count: number;
  records: DietRecord[];
}
