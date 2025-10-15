# hipaa_training/compliance_dashboard.py
import os
import json
import csv
from datetime import datetime
from pathlib import Path

class ComplianceDashboard:
    def __init__(self):
        self.reports_dir = "reports"
    
    def generate_enterprise_report(self, format_type):
        """Generate enterprise report in specified format."""
        valid_formats = ["csv", "json"]
        if format_type not in valid_formats:
            raise ValueError(f"Unsupported format: {format_type}. Supported formats: {valid_formats}")
        
        # Create reports directory
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.reports_dir}/enterprise_report_{timestamp}.{format_type}"
        
        # Generate report content based on format
        if format_type == "csv":
            self._generate_csv_report(filename)
        else:  # json
            self._generate_json_report(filename)
        
        return filename
    
    def _generate_csv_report(self, filename):
        """Generate CSV format report."""
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['User ID', 'Training Completed', 'Score', 'Completion Date'])
            writer.writerow([1, 'Yes', 95, '2024-01-15'])
            writer.writerow([2, 'No', 0, 'N/A'])
    
    def _generate_json_report(self, filename):
        """Generate JSON format report."""
        report_data = {
            "report_type": "enterprise_training",
            "generated_at": datetime.now().isoformat(),
            "users": [
                {"user_id": 1, "training_completed": True, "score": 95, "completion_date": "2024-01-15"},
                {"user_id": 2, "training_completed": False, "score": 0, "completion_date": None}
            ]
        }
        with open(filename, 'w') as jsonfile:
            json.dump(report_data, jsonfile, indent=2)
