/**
 * Memory System Type Definitions
 *
 * Types for Architecture Memory and Troubleshoot Memory systems
 */

export interface ArchitectureItem {
  id: string;
  slug: string;
  title: string;
  ai_when_to_use: string[];
  ai_requirements: string;
  keywords: string[];
  children_slugs: string[];
  related_slugs: string[];
  linked_epic_ids: string[];
  tags: string[];
  created_on: string;
  last_updated_on: string;

  // Frontend-specific
  children?: ArchitectureItem[];
  related?: ArchitectureItem[];
}

export interface TroubleshootItem {
  id: string;
  slug: string;
  title: string;
  ai_use_case: string[];
  ai_solutions: string;
  keywords: string[];
  tags: string[];
  usage_count: number;
  success_count: number;
  created_on: string;
  last_updated_on: string;
}

export interface ArchitectureItemFormData {
  slug: string;
  title: string;
  ai_when_to_use: string[];
  ai_requirements: string;
  keywords: string[];
  children_slugs: string[];
  related_slugs: string[];
  linked_epic_ids: string[];
  tags: string[];
}

export interface TroubleshootItemFormData {
  slug: string;
  title: string;
  ai_use_case: string[];
  ai_solutions: string;
  keywords: string[];
  tags: string[];
}

export interface MemoryApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export interface ArchitectureContext {
  success: boolean;
  primary_item: any;
  children: any[];
  related: any[];
  token_usage: {
    primary_item: number;
    children: number;
    related: number;
    total: number;
  };
  truncation_applied: boolean;
  markdown_summary: string;
}

export interface TroubleshootMatch {
  slug: string;
  title: string;
  relevance_score: number;
  matched_use_cases: string[];
  solution_preview: string;
}