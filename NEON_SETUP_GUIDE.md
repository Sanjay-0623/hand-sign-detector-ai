# Neon Database Setup Guide

## Database Successfully Configured! ✓

Your Neon database has been set up with the following tables:

### Tables Created:
1. **users** - Stores user accounts (username, password)
2. **training_data** - Stores hand sign training data (landmarks, labels)

## Environment Variables Needed

### For Local Development (.env file):

```plaintext
DATABASE_URL=postgresql://neondb_owner:your-password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
SECRET_KEY=your-secret-key-here
