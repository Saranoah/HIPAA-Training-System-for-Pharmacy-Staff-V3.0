# setup_project.py
import os
import json

def setup_project():
    # Create necessary directories
    directories = [
        'data',
        'data/users', 
        'data/progress',
        'content',
        'logs'
    ]
    
    for dir_path in directories:
        os.makedirs(dir_path, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Create default config if needed
    config = {
        "admin_password": "change_this_in_production",
        "training_required": True,
        "compliance_threshold": 80
    }
    
    with open('data/config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("Project setup completed!")

if __name__ == "__main__":
    setup_project()
