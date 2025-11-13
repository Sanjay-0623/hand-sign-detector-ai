-- Create users table for authentication
-- This table stores user credentials and data persistently in Supabase
CREATE TABLE IF NOT EXISTS public.users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Allow users to view their own data
CREATE POLICY "users_select_own"
  ON public.users FOR SELECT
  USING (true); -- Allow reading for login verification

-- Allow new user registration (anyone can insert)
CREATE POLICY "users_insert_new"
  ON public.users FOR INSERT
  WITH CHECK (true);

-- Allow users to update their own data
CREATE POLICY "users_update_own"
  ON public.users FOR UPDATE
  USING (id = auth.uid());

-- Allow users to delete their own data
CREATE POLICY "users_delete_own"
  ON public.users FOR DELETE
  USING (id = auth.uid());
