"""
Health Data Export V2 — Multi-format export with FHIR, HL7, PDF, CSV
"""
from datetime import datetime
from typing import Dict, List, Optional
import uuid
import json


class HealthExportV2:
    EXPORT_FORMATS = {
        "fhir": {"name": "FHIR R4 (JSON)", "mime": "application/fhir+json", "description": "Fast Healthcare Interoperability Resources standard"},
        "hl7": {"name": "HL7 v2 (Pipe-delimited)", "mime": "text/hl7", "description": "Health Level 7 standard messaging format"},
        "csv": {"name": "CSV (Spreadsheet)", "mime": "text/csv", "description": "Comma-separated values for Excel/Google Sheets"},
        "pdf": {"name": "PDF Report", "mime": "application/pdf", "description": "Formatted health report document"},
        "json": {"name": "JSON (Raw Data)", "mime": "application/json", "description": "Complete raw data export"},
        "xml": {"name": "XML", "mime": "application/xml", "description": "Extensible Markup Language export"},
    }

    DATA_CATEGORIES = ["vitals", "medications", "conditions", "allergies", "immunizations", "lab_results", "imaging", "procedures", "encounters", "nutrition", "exercise", "sleep", "mental_health", "goals"]

    def __init__(self):
        self.export_history: Dict[str, List[dict]] = {}
        self.export_requests: Dict[str, dict] = {}

    def create_export(self, user_id: str, format: str, categories: List[str] = None, date_range_start: str = None, date_range_end: str = None, anonymize: bool = False) -> dict:
        if format not in self.EXPORT_FORMATS:
            return {"error": f"Unknown format: {format}. Valid: {list(self.EXPORT_FORMATS.keys())}"}
        
        export_id = str(uuid.uuid4())[:8]
        selected_categories = categories or self.DATA_CATEGORIES
        
        export = {
            "export_id": export_id,
            "user_id": user_id,
            "format": format,
            "format_name": self.EXPORT_FORMATS[format]["name"],
            "categories": selected_categories,
            "date_range": {"start": date_range_start, "end": date_range_end},
            "anonymized": anonymize,
            "status": "processing",
            "created_at": datetime.now().isoformat(),
        }
        
        self.export_requests[export_id] = export
        export["status"] = "completed"
        export["sample_data"] = self._generate_sample_export(format, selected_categories)
        export["completed_at"] = datetime.now().isoformat()
        
        self.export_history.setdefault(user_id, []).append(export)
        return export

    def _generate_sample_export(self, format: str, categories: List[str]) -> dict:
        if format == "fhir":
            return {
                "resourceType": "Bundle",
                "type": "collection",
                "entry": [{"resource": {"resourceType": cat.title(), "status": "current"}} for cat in categories[:3]],
            }
        elif format == "csv":
            return {"headers": ["Date", "Category", "Metric", "Value", "Unit"], "sample_rows": 5}
        elif format == "pdf":
            return {"pages": 2, "sections": categories[:5]}
        else:
            return {"categories_exported": len(categories)}

    def get_export_history(self, user_id: str, limit: int = 20) -> List[dict]:
        return self.export_history.get(user_id, [])[-limit:]

    def get_export_status(self, export_id: str) -> dict:
        return self.export_requests.get(export_id, {"error": "Export not found"})


health_export_v2 = HealthExportV2()
