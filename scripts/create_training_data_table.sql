-- Create training_data table to store hand sign training samples
CREATE TABLE IF NOT EXISTS training_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    username TEXT NOT NULL,
    label TEXT NOT NULL,
    landmarks JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster queries by user
CREATE INDEX IF NOT EXISTS idx_training_data_user_id ON training_data(user_id);
CREATE INDEX IF NOT EXISTS idx_training_data_username ON training_data(username);
CREATE INDEX IF NOT EXISTS idx_training_data_label ON training_data(label);

-- Add comment
COMMENT ON TABLE training_data IS 'Stores hand sign training data with normalized landmark coordinates';
