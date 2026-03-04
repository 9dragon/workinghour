"""
Database migration script: Add budget management feature
Add role field to employees table and create project_budgets table
"""
import sqlite3
import os

def migrate():
    """Execute database migration"""
    # Get database file path
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'workinghour.db')

    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. Check if employees table has role field, add if not
        cursor.execute("PRAGMA table_info(employees)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'role' not in columns:
            print("Adding employees.role field...")
            cursor.execute("""
                ALTER TABLE employees
                ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'staff'
            """)
            # Set default role for existing employees
            cursor.execute("""
                UPDATE employees
                SET role = 'staff'
                WHERE role IS NULL OR role = ''
            """)
            print("OK - employees.role field added successfully")
        else:
            print("OK - employees.role field already exists")

        # 2. Check if project_budgets table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='project_budgets'")
        if not cursor.fetchone():
            print("Creating project_budgets table...")
            cursor.execute("""
                CREATE TABLE project_budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name VARCHAR(100) NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    budget_hours NUMERIC(10, 2) NOT NULL DEFAULT 0,
                    fiscal_year VARCHAR(10) NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    UNIQUE(project_name, role, fiscal_year)
                )
            """)

            # Create indexes
            cursor.execute("""
                CREATE INDEX idx_project_budgets_project_name
                ON project_budgets(project_name)
            """)
            cursor.execute("""
                CREATE INDEX idx_project_budgets_fiscal_year
                ON project_budgets(fiscal_year)
            """)

            print("OK - project_budgets table created successfully")
        else:
            print("OK - project_budgets table already exists")

        conn.commit()
        print("\nDatabase migration completed successfully!")
        return True

    except Exception as e:
        conn.rollback()
        print(f"\nDatabase migration failed: {e}")
        return False
    finally:
        conn.close()


def rollback():
    """Rollback database migration"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'workinghour.db')

    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Starting database migration rollback...")

        # Drop project_budgets table
        cursor.execute("DROP TABLE IF EXISTS project_budgets")
        print("OK - project_budgets table dropped")

        # SQLite doesn't support dropping columns directly
        # We just mark the role field as unused, no actual deletion
        print("WARNING: SQLite doesn't support dropping columns, employees.role field will remain but unused")

        conn.commit()
        print("\nDatabase migration rollback completed!")
        return True

    except Exception as e:
        conn.rollback()
        print(f"\nDatabase migration rollback failed: {e}")
        return False
    finally:
        conn.close()


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        rollback()
    else:
        migrate()
