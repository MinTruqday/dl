export interface ExploreAuthor {
  full_name?: string;
  username?: string;
}

export interface ExploreDocument {
  _id?: string;
  slug: string;
  title: string;
  cover_url?: string;
  categories?: string[];
  author?: ExploreAuthor;
  created_at?: string;
  views_count?: number;
  average_rating?: number;
  chapters_count?: number;
  is_premium?: boolean;
  price?: number;
}

export type ExploreView = "grid" | "list";
