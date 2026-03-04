"""
Remove fiscal_year from project_budgets table

This migration removes the fiscal_year column and updates the unique constraint
from (project_code, budget_type, fiscal_year) to (project_code, budget_type).
"""
import sqlite3
import os
from datetime import datetime


def get_db_path():
    """Get the database path"""
    # Default path for development
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'working_hours.db')
    if not os.path.exists(db_path):
        # Try alternative path
        db_path = os.path.join(os.path.dirname(__file__), '..', 'working_hours.db')
    return db_path


def migrate():
    """Execute the migration"""
    db_path = get_db_path()

    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Starting migration: Remove fiscal_year from project_budgets")

        # Check if the table and column exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='project_budgets'")
        if not cursor.fetchone():
            print("Table project_budgets does not exist. Skipping migration.")
            return True

        cursor.execute("PRAGMA table_info(project_budgets)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'fiscal_year' not in columns:
            print("Column fiscal_year does not exist. Skipping migration.")
            return True

        # Step 1: Get existing data to handle potential duplicates
        print("Checking for duplicate records...")
        cursor.execute("""
            SELECT project_code, budget_type, fiscal_year,
                   SUM(budget_hours) as total_hours,
                   MAX(id) as keep_id
            FROM project_budgets
            GROUP BY project_code, budget_type
            HAVING COUNT(*) > 1
        """)

        duplicates = cursor.fetchall()

        if duplicates:
            print(f"Found {len(duplicates)} duplicate (project_code, budget_type) combinations.")
            print("Merging duplicate records by summing budget_hours...")

            for dup in duplicates:
                project_code, budget_type, fiscal_year, total_hours, keep_id = dup
                # Delete all but the one with highest id, then update the remaining one with summed hours
                cursor.execute("""
                    UPDATE project_budgets
                    SET budget_hours = ?
                    WHERE id = ?
                """, (total_hours, keep_id))

                cursor.execute("""
                    DELETE FROM project_budgets
                    WHERE project_code = ? AND budget_type = ? AND id != ?
                """, (project_code, budget_type, keep_id))

        # Step 2: Create new table without fiscal_year
        print("Creating new table structure...")
        cursor.execute("""
            CREATE TABLE project_budgets_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name VARCHAR(100) NOT NULL,
                project_code VARCHAR(20) NOT NULL,
                budget_type VARCHAR(20) NOT NULL,
                budget_hours NUMERIC(10, 2) NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                UNIQUE (project_code, budget_type)
            )
        """)

        # Step 3: Copy data from old table to new table
        print("Copying data to new table...")
        cursor.execute("""
            INSERT INTO project_budgets_new (id, project_name, project_code, budget_type, budget_hours, created_at, updated_at)
            SELECT id, project_name, project_code, budget_type, budget_hours, created_at, updated_at
            FROM project_budgets
        """)

        # Step 4: Drop old table and rename new table
        print("Replacing old table...")
        cursor.execute("DROP TABLE project_budgets")
        cursor.execute("ALTER TABLE project_budgets_new RENAME TO project_budgets")

        # Step 5: Create indexes
        print("Creating indexes...")
        cursor.execute("CREATE INDEX idx_project_budgets_project_code ON project_budgets(project_code)")
        cursor.execute("CREATE INDEX idx_project_budgets_budget_type ON project_budgets(budget_type)")

        conn.commit()
        print("Migration completed successfully!")
        return True

    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        return False
    finally:
        conn.close()


def rollback():
    """Rollback the migration (re-add fiscal_year column)"""
    db_path = get_db_path()

    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Rolling back: Add fiscal_year to project_budgets")

        # Check if fiscal_year already exists
        cursor.execute("PRAGMA table_info(project_budgets)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'fiscal_year' in columns:
            print("Column fiscal_year already exists. Skipping rollback.")
            return True

        # Add fiscal_year column
        cursor.execute("ALTER TABLE project_budgets ADD COLUMN fiscal_year VARCHAR(10) NOT NULL DEFAULT '2026'")

        # Recreate table with fiscal_year in unique constraint
        cursor.execute("""
            CREATE TABLE project_budgets_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name VARCHAR(100) NOT NULL,
                project_code VARCHAR(20) NOT NULL,
                budget_type VARCHAR(20) NOT NULL,
                budget_hours NUMERIC(10, 2) NOT NULL DEFAULT 0,
                fiscal_year VARCHAR(10) NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                UNIQUE (project_code, budget_type, fiscal_year)
            )
        """)

        cursor.execute("""
            INSERT INTO project_budgets_new (id, project_name, project_code, budget_type, budget_hours, fiscal_year, created_at, updated_at)
            SELECT id, project_name, project_code, budget_type, budget_hours, fiscal_year, created_at, updated_at
            FROM project_budgets
        """)

        cursor.execute("DROP TABLE project_budgets")
        cursor.execute("ALTER TABLE project_budgets_new RENAME TO project_budgets")

        cursor.execute("CREATE INDEX idx_project_budgets_project_code ON project_budgets(project_code)")
        cursor.execute("CREATE INDEX idx_project_budgets_budget_type ON project_budgets(budget_type)")
        cursor.execute("CREATE INDEX idx_project_budgets_fiscal_year ON project_budgets(fiscal_year)")

        conn.commit()
        print("Rollback completed successfully!")
        return True

    except Exception as e:
        conn.rollback()
        print(f"Rollback failed: {e}")
        return False
    finally:
        conn.close()


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        rollback()
    else:
        migrate()
