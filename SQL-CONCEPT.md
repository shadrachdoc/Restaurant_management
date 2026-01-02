# SQL Migration Concepts - From Basic to Advanced

**A complete guide to understanding database migrations and why they're essential**

---

## Table of Contents

1. [What is a Database Schema?](#what-is-a-database-schema)
2. [The Problem: Schema Evolution](#the-problem-schema-evolution)
3. [What are Database Migrations?](#what-are-database-migrations)
4. [Why We Need Migrations](#why-we-need-migrations)
5. [Migration Methods](#migration-methods)
6. [SQLAlchemy vs Alembic](#sqlalchemy-vs-alembic)
7. [Real Example from Our System](#real-example-from-our-system)
8. [Best Practices](#best-practices)

---

## What is a Database Schema?

### Basic Concept

A **database schema** is like a blueprint for your database. It defines:
- **Tables** - Where data is stored (like spreadsheets)
- **Columns** - Fields in each table (like spreadsheet columns)
- **Data types** - What kind of data each column holds (text, numbers, dates)
- **Constraints** - Rules for the data (required, unique, etc.)
- **Relationships** - How tables connect to each other

### Example: Restaurant Orders Table

```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY,
    restaurant_id UUID NOT NULL,
    customer_name VARCHAR(255),
    total FLOAT,
    created_at TIMESTAMP
);
```

This creates a table called `orders` with 5 columns:
- `id` - Unique identifier for each order
- `restaurant_id` - Which restaurant the order belongs to
- `customer_name` - Name of the customer
- `total` - Total price
- `created_at` - When the order was created

---

## The Problem: Schema Evolution

### The Challenge

Imagine you build an application and deploy it to production. Later, you need to add new features. This requires **changing the database schema**.

### Example Scenario

**Version 1** - Initial orders table:
```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY,
    restaurant_id UUID NOT NULL,
    customer_name VARCHAR(255),
    total FLOAT,
    created_at TIMESTAMP
);
```

**Version 2** - You want to add online ordering, so you need to track order type:
```sql
-- Need to add this column:
ALTER TABLE orders ADD COLUMN order_type VARCHAR(50);
```

### The Problems Without Migrations

❌ **Problem 1: Manual Changes**
```bash
# On development database
psql -d dev_db -c "ALTER TABLE orders ADD COLUMN order_type VARCHAR(50);"

# On production database (manual, error-prone!)
psql -d prod_db -c "ALTER TABLE orders ADD COLUMN order_type VARCHAR(50);"

# On testing database
psql -d test_db -c "ALTER TABLE orders ADD COLUMN order_type VARCHAR(50);"
```

**Issues:**
- Easy to forget which changes were made
- No record of what changed when
- Different environments can have different schemas
- Can't easily rollback changes
- Multiple developers = chaos!

❌ **Problem 2: Existing Data**
```sql
-- New code expects order_type to exist
INSERT INTO orders (id, restaurant_id, customer_name, total, order_type)
VALUES (...);

-- But if database doesn't have order_type column yet:
ERROR: column "order_type" does not exist
```

❌ **Problem 3: Team Collaboration**
```
Developer A: "It works on my machine!"
Developer B: "Getting errors about missing column..."
DBA: "Production database is different from dev..."
```

---

## What are Database Migrations?

### Definition

**Database migrations** are version-controlled, incremental changes to your database schema.

Think of migrations like **Git commits for your database**:
- Each migration is a numbered file
- Shows what changed and when
- Can be applied in order
- Can be rolled back if needed
- Everyone on the team has the same changes

### Migration Anatomy

A migration file has two parts:

**1. Upgrade (Forward Migration)**
```python
def upgrade():
    """What to do when applying this migration"""
    op.add_column('orders',
        sa.Column('order_type', sa.String(50), nullable=True)
    )
```

**2. Downgrade (Rollback)**
```python
def downgrade():
    """What to do when rolling back this migration"""
    op.drop_column('orders', 'order_type')
```

---

## Why We Need Migrations

### 1. **Version Control for Database**

Just like Git tracks code changes, migrations track database changes:

```
migrations/
├── 001_initial_schema.py          # Created orders table
├── 002_add_order_type.py          # Added order_type column
├── 003_add_analytics_fields.py   # Added analytics columns
└── 004_add_indexes.py             # Added performance indexes
```

### 2. **Reproducibility**

Everyone gets the same database structure:

```bash
# Developer 1
alembic upgrade head  # Applies all migrations

# Developer 2
alembic upgrade head  # Gets exact same schema

# Production server
alembic upgrade head  # Production matches dev!
```

### 3. **Safe Changes**

Migrations can handle complex changes safely:

```python
# Example: Renaming a column safely
def upgrade():
    # 1. Add new column
    op.add_column('orders', sa.Column('customer_full_name', sa.String(255)))

    # 2. Copy data from old column
    op.execute('UPDATE orders SET customer_full_name = customer_name')

    # 3. Remove old column
    op.drop_column('orders', 'customer_name')
```

### 4. **Rollback Capability**

If something goes wrong:

```bash
# Apply migration
alembic upgrade head
# Output: Applied migration 003

# Oh no! Something broke!
alembic downgrade -1
# Output: Rolled back migration 003
```

### 5. **Documentation**

Migrations are living documentation:

```python
"""
Migration: Add analytics fields and indexes

Date: 2025-12-27 14:30
Author: Developer Team

Changes:
- Added order_type column for tracking TABLE/DELIVERY/TAKEOUT
- Added preparation_time column for kitchen analytics
- Added completed_at column for performance tracking
- Added indexes for faster queries

Why: Enable analytics dashboard and ML predictions
"""
```

---

## Migration Methods

### Method 1: Manual SQL Scripts (Old Way)

**How it works:**
```bash
# Create SQL file manually
cat > 001_add_order_type.sql << EOF
ALTER TABLE orders ADD COLUMN order_type VARCHAR(50);
EOF

# Run manually on each database
psql -d mydb -f 001_add_order_type.sql
```

**Problems:**
- ❌ No automatic tracking
- ❌ No rollback
- ❌ Manual execution
- ❌ No validation

### Method 2: ORM create_all() (Basic Way)

**How it works:**
```python
# In your code
from database import Base, engine

# Create all tables from models
Base.metadata.create_all(engine)
```

**What happens:**
```python
# If you have this model:
class Order(Base):
    __tablename__ = 'orders'
    id = Column(UUID, primary_key=True)
    customer_name = Column(String(255))
    total = Column(Float)
```

SQLAlchemy generates:
```sql
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY,
    customer_name VARCHAR(255),
    total FLOAT
);
```

**Problems:**
- ❌ Only creates tables, doesn't modify existing ones
- ❌ No version tracking
- ❌ Can't handle complex changes
- ❌ No rollback

**Example of the problem:**
```python
# Version 1: Model has 3 columns
class Order(Base):
    id = Column(UUID)
    customer_name = Column(String)
    total = Column(Float)

Base.metadata.create_all(engine)  # Creates table with 3 columns

# Version 2: Add new column to model
class Order(Base):
    id = Column(UUID)
    customer_name = Column(String)
    total = Column(Float)
    order_type = Column(String)  # NEW!

Base.metadata.create_all(engine)  # Does NOTHING! Table already exists!
```

### Method 3: Alembic Migrations (Modern Way) ✅

**How it works:**
```bash
# 1. Initialize Alembic
alembic init alembic

# 2. Generate migration from model changes
alembic revision --autogenerate -m "Add order_type column"

# 3. Review generated migration
# File: alembic/versions/001_add_order_type.py
def upgrade():
    op.add_column('orders', sa.Column('order_type', sa.String(50)))

def downgrade():
    op.drop_column('orders', 'order_type')

# 4. Apply migration
alembic upgrade head
```

**Benefits:**
- ✅ Automatic tracking
- ✅ Rollback support
- ✅ Version control
- ✅ Team collaboration
- ✅ Production-safe

---

## SQLAlchemy vs Alembic

### SQLAlchemy (ORM)

**Purpose:** Work with database in Python code

**What it does:**
```python
# Define models
class Order(Base):
    __tablename__ = 'orders'
    id = Column(UUID, primary_key=True)
    customer_name = Column(String(255))

# Query data
orders = session.query(Order).filter(Order.total > 100).all()

# Insert data
new_order = Order(customer_name="John", total=50.0)
session.add(new_order)
session.commit()
```

**Can create initial schema:**
```python
Base.metadata.create_all(engine)  # Creates all tables
```

**Cannot:**
- Modify existing tables
- Track schema versions
- Provide rollback
- Handle complex migrations

### Alembic (Migration Tool)

**Purpose:** Manage database schema changes over time

**What it does:**
```python
# Generate migration
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head

# Rollback migrations
alembic downgrade -1

# Check current version
alembic current

# View migration history
alembic history
```

### When to Use What

| Task | Use |
|------|-----|
| Define data models | SQLAlchemy |
| Query/insert/update data | SQLAlchemy |
| Create initial schema | SQLAlchemy OR Alembic |
| Modify existing schema | Alembic |
| Track schema changes | Alembic |
| Rollback changes | Alembic |
| Production deployments | Alembic |

### They Work Together

```python
# 1. Define model with SQLAlchemy
class Order(Base):
    __tablename__ = 'orders'
    id = Column(UUID, primary_key=True)
    order_type = Column(String(50))  # NEW COLUMN!

# 2. Generate migration with Alembic
# $ alembic revision --autogenerate -m "Add order_type"

# 3. Alembic reads SQLAlchemy models and generates:
def upgrade():
    op.add_column('orders',
        sa.Column('order_type', sa.String(50), nullable=True)
    )

# 4. Apply migration
# $ alembic upgrade head

# 5. Now use SQLAlchemy to work with new column
order = Order(order_type="TABLE")
session.add(order)
```

---

## Real Example from Our System

### What Happened in Our Restaurant System

**Timeline:**

**Day 1: Initial Development**
```python
# Created Order model
class Order(Base):
    __tablename__ = 'orders'
    id = Column(UUID, primary_key=True)
    restaurant_id = Column(UUID)
    customer_name = Column(String(255))
    total = Column(Float)
    created_at = Column(DateTime)

# Used create_all() to create tables
Base.metadata.create_all(engine)
```

Database has:
```sql
orders table:
- id
- restaurant_id
- customer_name
- total
- created_at
```

**Day 30: Added Analytics Feature**
```python
# Updated Order model for analytics
class Order(Base):
    __tablename__ = 'orders'
    id = Column(UUID, primary_key=True)
    restaurant_id = Column(UUID)
    customer_name = Column(String(255))
    total = Column(Float)
    created_at = Column(DateTime)
    # NEW COLUMNS for analytics:
    order_type = Column(Enum('TABLE', 'DELIVERY', 'TAKEOUT'))  # NEW!
    preparation_time = Column(Integer)  # NEW!
    completed_at = Column(DateTime)  # NEW!

# create_all() does NOTHING - table already exists!
Base.metadata.create_all(engine)
```

**Day 60: Recreated Database (Issue #9)**
```bash
# Had to delete PostgreSQL PVC due to node failure
kubectl delete pvc postgres-storage-postgres-0

# PostgreSQL restarted with empty database
# Services started and ran create_all()
Base.metadata.create_all(engine)
```

**Result:**
- `create_all()` created tables from **latest model**
- Orders table had: id, restaurant_id, customer_name, total, created_at
- **MISSING:** order_type, preparation_time, completed_at
- These columns were in the model but never added to database!

**Day 61: User Tried to Place Order**
```python
# Code tries to insert with order_type
new_order = Order(
    order_type="TABLE",  # Column doesn't exist in DB!
    customer_name="Guest"
)
session.add(new_order)
session.commit()

# ERROR!
sqlalchemy.exc.ProgrammingError: column "order_type" does not exist
```

### The Solution: Run Alembic Migration

**Migration File:** `20251227_1430_001_add_analytics_fields_and_indexes.py`

```python
def upgrade():
    """Add analytics fields to orders table"""

    # Add order_type enum
    op.execute("CREATE TYPE ordertype AS ENUM ('TABLE', 'DELIVERY', 'TAKEOUT')")
    op.add_column('orders',
        sa.Column('order_type', sa.Enum('TABLE', 'DELIVERY', 'TAKEOUT'))
    )

    # Add analytics columns
    op.add_column('orders',
        sa.Column('preparation_time', sa.Integer(), nullable=True)
    )
    op.add_column('orders',
        sa.Column('completed_at', sa.DateTime(), nullable=True)
    )

    # Add indexes for performance
    op.create_index('ix_orders_order_type', 'orders', ['order_type'])
    op.create_index('ix_orders_completed_at', 'orders', ['completed_at'])

def downgrade():
    """Remove analytics fields"""
    op.drop_index('ix_orders_completed_at')
    op.drop_index('ix_orders_order_type')
    op.drop_column('orders', 'completed_at')
    op.drop_column('orders', 'preparation_time')
    op.drop_column('orders', 'order_type')
    op.execute('DROP TYPE ordertype')
```

**Running the migration:**
```bash
# Inside order-service pod
kubectl exec -n restaurant-system order-service-pod -c order-service -- \
  alembic upgrade head

# Output:
INFO [alembic.runtime.migration] Running upgrade  -> 001, Add analytics fields
```

**Result:**
- ✅ order_type column added
- ✅ preparation_time column added
- ✅ completed_at column added
- ✅ Indexes created
- ✅ Orders can now be placed!

---

## Best Practices

### 1. **Always Use Migrations for Schema Changes**

❌ **Don't:**
```python
# Don't rely on create_all() for updates
Base.metadata.create_all(engine)  # Only works for initial creation
```

✅ **Do:**
```bash
# Use Alembic for all schema changes
alembic revision --autogenerate -m "Description of change"
alembic upgrade head
```

### 2. **Run Migrations on Application Startup**

**Option A: Automatic (Development)**
```python
# In main.py startup
async def lifespan(app: FastAPI):
    logger.info("Running database migrations...")
    subprocess.run(["alembic", "upgrade", "head"])
    logger.info("Migrations complete")
    yield
```

**Option B: Manual (Production)**
```bash
# In deployment script
echo "Running migrations..."
kubectl exec $POD_NAME -- alembic upgrade head
echo "Starting application..."
kubectl rollout restart deployment/order-service
```

### 3. **Version Your Migrations**

```
alembic/versions/
├── 001_initial_schema.py
├── 002_add_order_type.py
├── 003_add_analytics_fields.py  ← Current
```

### 4. **Test Migrations Before Production**

```bash
# On dev environment
alembic upgrade head
# Test application...
# If issues found:
alembic downgrade -1  # Rollback
# Fix migration
# Try again
```

### 5. **Never Edit Applied Migrations**

❌ **Don't:**
```python
# Migration already applied in production
def upgrade():
    op.add_column('orders', sa.Column('status', sa.String(50)))
    # DON'T edit this!
```

✅ **Do:**
```bash
# Create NEW migration
alembic revision -m "Fix status column type"
```

### 6. **Keep Migrations Small and Focused**

❌ **Don't:**
```python
# One huge migration doing everything
def upgrade():
    # Add 10 columns
    # Create 5 indexes
    # Modify 3 relationships
    # Update all existing data
    # ... 500 lines ...
```

✅ **Do:**
```python
# Migration 001: Add columns
def upgrade():
    op.add_column('orders', sa.Column('order_type', sa.String(50)))

# Migration 002: Add indexes
def upgrade():
    op.create_index('ix_orders_type', 'orders', ['order_type'])

# Migration 003: Migrate data
def upgrade():
    op.execute("UPDATE orders SET order_type = 'TABLE' WHERE order_type IS NULL")
```

### 7. **Always Provide Downgrade**

```python
def upgrade():
    op.add_column('orders', sa.Column('new_field', sa.String(50)))

def downgrade():
    op.drop_column('orders', 'new_field')  # Always provide rollback!
```

---

## Quick Command Reference

### Alembic Commands

```bash
# Initialize Alembic in project
alembic init alembic

# Create new migration (manual)
alembic revision -m "Description"

# Create new migration (auto-detect changes)
alembic revision --autogenerate -m "Description"

# Apply all pending migrations
alembic upgrade head

# Apply specific number of migrations
alembic upgrade +2

# Rollback one migration
alembic downgrade -1

# Rollback all migrations
alembic downgrade base

# Show current version
alembic current

# Show migration history
alembic history

# Show SQL without applying
alembic upgrade head --sql
```

### PostgreSQL Commands

```bash
# List all tables
\dt

# Describe table structure
\d table_name

# Show all columns in a table
\d+ table_name

# List all databases
\l

# Connect to database
\c database_name
```

---

## Summary

### Key Takeaways

1. **Database Schema = Blueprint** of your database structure

2. **create_all() = Initial Creation Only**
   - Creates tables if they don't exist
   - Does NOT modify existing tables
   - No version tracking
   - Use for: First-time setup only

3. **Alembic Migrations = Version Control for Database**
   - Tracks all changes over time
   - Can upgrade and rollback
   - Works across environments
   - Use for: All schema changes

4. **Why Our System Failed**
   - Used `create_all()` for initial creation ✅
   - Added new columns to models ✅
   - Recreated database (lost data) ⚠️
   - `create_all()` didn't add new columns ❌
   - **Migrations never ran** ❌
   - Application expected columns that didn't exist ❌

5. **The Fix**
   - Ran Alembic migrations ✅
   - Added missing columns ✅
   - Application now works ✅

### Remember

> **SQLAlchemy** = How you work with data in code
>
> **Alembic** = How you change database structure over time
>
> **Always use migrations for schema changes in production!**

---

## For Production

When deploying to production laptop, **MUST run migrations**:

```bash
# After setting up PostgreSQL
kubectl exec -n restaurant-system order-service-pod -- alembic upgrade head
kubectl exec -n restaurant-system auth-service-pod -- alembic upgrade head
kubectl exec -n restaurant-system restaurant-service-pod -- alembic upgrade head
kubectl exec -n restaurant-system customer-service-pod -- alembic upgrade head
```

This ensures all database tables have the correct schema with all columns!
