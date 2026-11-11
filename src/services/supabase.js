import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error("❌ VITE_SUPABASE_URL atau VITE_SUPABASE_ANON_KEY tak ada");
  console.log("URL:", supabaseUrl);
  console.log("Key:", supabaseKey);
}

export const supabase = createClient(supabaseUrl, supabaseKey);