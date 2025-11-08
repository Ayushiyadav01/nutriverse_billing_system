#!/usr/bin/env python3

import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db import init_db
from app.sample_data import create_all_sample_data

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    
    # Ask if sample data should be created
    create_samples = input("Create sample data? (y/n): ").lower().strip() == 'y'
    
    if create_samples:
        print("Creating sample data...")
        success = create_all_sample_data()
        if success:
            print("Sample data created successfully!")
        else:
            print("Failed to create sample data.")
    
    print("Database initialization complete.")

