-- PostgreSQL Database Initialization Script
-- Restaurant Management System

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- Create schemas for separation (optional)
-- CREATE SCHEMA IF NOT EXISTS auth;
-- CREATE SCHEMA IF NOT EXISTS restaurant;
-- CREATE SCHEMA IF NOT EXISTS orders;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE restaurant_db TO restaurant_admin;

-- Create enums
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('master_admin', 'restaurant_admin', 'chef', 'customer');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE order_status AS ENUM ('pending', 'confirmed', 'preparing', 'ready', 'served', 'cancelled', 'completed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE table_status AS ENUM ('available', 'occupied', 'reserved', 'cleaning');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE pricing_plan AS ENUM ('per_table', 'basic', 'premium', 'enterprise');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE subscription_status AS ENUM ('active', 'inactive', 'suspended', 'trial', 'expired');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE menu_item_category AS ENUM ('appetizer', 'main_course', 'dessert', 'beverage', 'side_dish', 'special');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create a function for full-text search (for menu items, restaurants, etc.)
CREATE OR REPLACE FUNCTION create_search_trigger(table_name text, column_name text)
RETURNS void AS $$
BEGIN
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I USING gin(%I gin_trgm_ops)',
                   table_name || '_' || column_name || '_search_idx',
                   table_name,
                   column_name);
END;
$$ LANGUAGE plpgsql;

-- Initial admin user will be created by the auth service on first run

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Database initialized successfully for Restaurant Management System';
END $$;
