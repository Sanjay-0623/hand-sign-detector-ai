-- Completely disable RLS on users table
-- This must be run in your Supabase SQL Editor to fix authentication

-- Drop all existing policies
DROP POLICY IF EXISTS users_delete_own ON users;
DROP POLICY IF EXISTS users_insert_new ON users;
DROP POLICY IF EXISTS users_select_own ON users;
DROP POLICY IF EXISTS users_update_own ON users;

-- Disable RLS completely
ALTER TABLE users DISABLE ROW LEVEL SECURITY;

-- Verify RLS is disabled
SELECT 
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables 
WHERE schemaname = 'public' AND tablename = 'users';
