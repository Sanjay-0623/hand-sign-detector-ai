-- Disable Row Level Security for users table
-- This is needed because we're using custom authentication, not Supabase Auth

-- Drop all existing policies first
DROP POLICY IF EXISTS users_delete_own ON users;
DROP POLICY IF EXISTS users_insert_new ON users;
DROP POLICY IF EXISTS users_select_own ON users;
DROP POLICY IF EXISTS users_update_own ON users;

-- Disable RLS entirely on the users table
ALTER TABLE users DISABLE ROW LEVEL SECURITY;

-- Verify the change
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' AND tablename = 'users';
