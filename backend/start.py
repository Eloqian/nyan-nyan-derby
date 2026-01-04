import subprocess
import sys
import os

def main():
    print("Initializing application...")
    
    print("Running database migrations...")
    
    # Check if we need to generate initial migration
    versions_dir = os.path.join(os.getcwd(), "alembic", "versions")
    if not os.path.exists(versions_dir):
        os.makedirs(versions_dir)
        
    # Check if there are any python migration files (ignoring __pycache__)
    migration_files = [f for f in os.listdir(versions_dir) if f.endswith('.py')]
    
    if not migration_files:
        print("No migrations found. Generating initial migration...")
        try:
             subprocess.run([sys.executable, "-m", "alembic", "revision", "--autogenerate", "-m", "Initial migration"], check=True)
        except subprocess.CalledProcessError as e:
             print(f"Failed to generate migration: {e}")
             
    try:
        # Using python -m alembic to avoid path issues
        result = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
        print("Migrations completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error during migrations: {e}")
        # We exit with error so Docker can restart/log it
        sys.exit(1)
        
    # Start Uvicorn
    print("Starting Uvicorn server...")
    # Using execvp to replace the process
    os.execvp("uvicorn", ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"])

if __name__ == "__main__":
    main()
