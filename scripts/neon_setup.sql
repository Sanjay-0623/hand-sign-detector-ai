-- Create training_data table in Neon
CREATE TABLE IF NOT EXISTS public.training_data (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL,
    label TEXT NOT NULL,
    landmarks JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_training_data_user_id ON public.training_data(user_id);
CREATE INDEX IF NOT EXISTS idx_training_data_label ON public.training_data(label);

-- Verify tables
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
