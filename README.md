... existing code ...

## Database Setup

// <CHANGE> Replaced Supabase with Neon database instructions
This application uses **Neon** (PostgreSQL) to store user accounts and training data. The database has already been configured and the tables are created.

### Environment Variables

The application requires the `DATABASE_URL` environment variable to connect to Neon.

**For Local Development (.env file):**

```plaintext
DATABASE_URL=postgresql://user:password@host.neon.tech/dbname?sslmode=require
SECRET_KEY=your-random-secret-key-here
