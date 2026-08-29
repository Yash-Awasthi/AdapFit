"""
Workplace Safety — OSHA Compliance, Incident Reporting, Safety Training
Hazard identification, ergonomic assessment, safety compliance tracking
"""
from datetime import datetime, timedelta
from typing import Dict, List
import random


class WorkplaceSafetyService:
    """OSHA compliance and workplace safety platform"""

    def __init__(self):
        self.osha_standards = {
            "general_industry": {
                "subpart": "1910",
                "key_standards": [
                    {"id": "1910.22", "title": "Walking-Working Surfaces", "frequency": "annual"},
                    {"id": "1910.38", "title": "Emergency Action Plans", "frequency": "annual"},
                    {"id": "1910.95", "title": "Occupational Noise Exposure", "frequency": "annual"},
                    {"id": "1910.134", "title": "Respiratory Protection", "frequency": "annual"},
                    {"id": "1910.147", "title": "Lockout/Tagout", "frequency": "annual"},
                    {"id": "1910.1030", "title": "Bloodborne Pathogens", "frequency": "annual"},
                    {"id": "1910.1200", "title": "Hazard Communication", "frequency": "annual"},
                ],
            },
            "construction": {
                "subpart": "1926",
                "key_standards": [
                    {"id": "1926.20", "title": "General Safety and Health", "frequency": "daily"},
                    {"id": "1926.50", "title": "Medical Services and First Aid", "frequency": "annual"},
                    {"id": "1926.451", "title": "Scaffolding", "frequency": "daily"},
                    {"id": "1926.502", "title": "Fall Protection", "frequency": "daily"},
                    {"id": "1926.1052", "title": "Stairways and Ladders", "frequency": "daily"},
                ],
            },
        }

        self.hazard_categories = {
            "physical": ["slippery floors", "uneven surfaces", "exposed wiring", "falling objects", "noise", "vibration"],
            "chemical": ["cleaning agents", "solvents", "paint fumes", "dust", "gases"],
            "biological": ["bloodborne pathogens", "mold", "pests", "sick coworkers"],
            "ergonomic": ["repetitive motion", "poor posture", "heavy lifting", "vibration", "awkward positions"],
            "psychosocial": ["workplace violence", "bullying", "stress", "burnout", "shift work"],
        }

        self.incident_severities = {
            "near_miss": {"description": "Event that could have caused injury", "reporting": "within 24 hours", "investigation": "supervisor"},
            "first_aid": {"description": "Minor injury requiring first aid only", "reporting": "immediate", "investigation": "supervisor"},
            "medical_treatment": {"description": "Injury requiring medical treatment beyond first aid", "reporting": "immediate", "investigation": "safety_manager"},
            "lost_time": {"description": "Injury resulting in missed work days", "reporting": "immediate", "investigation": "safety_team"},
            "hospitalization": {"description": "Injury requiring hospitalization", "reporting": "immediate_osha", "investigation": "management"},
            "fatality": {"description": "Workplace death", "reporting": "immediate_osha_8hr", "investigation": "management_external"},
        }

    def report_incident(self, incident_data: Dict) -> Dict:
        """Report a workplace incident"""
        severity = incident_data.get("severity", "near_miss")
        incident_info = self.incident_severities.get(severity, self.incident_severities["near_miss"])

        return {
            "incident_id": f"INC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "reported_at": datetime.now().isoformat(),
            "severity": severity,
            "description": incident_data.get("description", ""),
            "location": incident_data.get("location", ""),
            "injured_person": incident_data.get("injured_person", ""),
            "witnesses": incident_data.get("witnesses", []),
            "immediate_actions": incident_data.get("immediate_actions", ""),
            "reporting_deadline": incident_info["reporting"],
            "investigation_by": incident_info["investigation"],
            "osha_reporting_required": severity in ["hospitalization", "fatality"],
            "follow_up_actions": self._get_follow_up_actions(severity),
            "corrective_actions_needed": True,
        }

    def _get_follow_up_actions(self, severity: str) -> List[str]:
        """Get follow-up actions based on severity"""
        actions = ["Document the incident", "Notify supervisor"]
        if severity in ["medical_treatment", "lost_time"]:
            actions.extend(["Complete incident investigation", "Implement corrective actions", "Review safety procedures"])
        if severity == "hospitalization":
            actions.extend(["OSHA notification within 24 hours", "Root cause analysis", "Management review"])
        if severity == "fatality":
            actions.extend(["OSHA notification within 8 hours", "Preserve scene", "External investigation"])
        return actions

    def conduct_inspection(self, inspection_data: Dict) -> Dict:
        """Conduct a workplace safety inspection"""
        area = inspection_data.get("area", "general")
        findings = []

        # Generate findings based on common hazards
        common_findings = [
            {"finding": "Missing fire extinguisher inspection tag", "severity": "medium", "standard": "1910.157", "corrective": "Inspect and tag fire extinguishers"},
            {"finding": "Exit path partially blocked", "severity": "high", "standard": "1910.37", "corrective": "Clear exit path immediately"},
            {"finding": "Missing safety data sheets for chemicals", "severity": "medium", "standard": "1910.1200", "corrective": "Update SDS binder"},
            {"defect": "Emergency lighting not functioning", "severity": "medium", "standard": "1910.37", "corrective": "Replace emergency lights"},
        ]

        num_findings = random.randint(1, 4)
        selected_findings = random.sample(common_findings, min(num_findings, len(common_findings)))
        for i, finding in enumerate(selected_findings):
            findings.append({
                "id": i + 1,
                "finding": finding.get("finding", finding.get("defect", "")),
                "severity": finding["severity"],
                "standard": finding["standard"],
                "corrective_action": finding["corrective"],
                "assigned_to": inspection_data.get("inspector", "Safety Manager"),
                "due_date": (datetime.now() + timedelta(days=30 if finding["severity"] == "low" else 14 if finding["severity"] == "medium" else 7)).strftime("%Y-%m-%d"),
            })

        compliance_score = max(0, 100 - len(findings) * 15)

        return {
            "inspection_id": f"INS-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "inspection_date": datetime.now().isoformat(),
            "area_inspected": area,
            "inspector": inspection_data.get("inspector", "Safety Manager"),
            "findings": findings,
            "findings_count": len(findings),
            "compliance_score": compliance_score,
            "status": "compliant" if compliance_score >= 80 else "needs_correction",
            "next_inspection_due": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d"),
        }

    def get_safety_training(self, role: str) -> Dict:
        """Get required safety training for a role"""
        trainings = {
            "all_employees": [
                {"name": "Emergency Action Plan", "duration": "1 hour", "frequency": "annual", "osha_required": True},
                {"name": "Fire Prevention", "duration": "30 minutes", "frequency": "annual", "osha_required": True},
                {"name": "Hazard Communication", "duration": "1 hour", "frequency": "annual", "osha_required": True},
                {"name": "Active Shooter Response", "duration": "1 hour", "frequency": "annual", "osha_required": False},
            ],
            "supervisor": [
                {"name": "Incident Investigation", "duration": "2 hours", "frequency": "annual", "osha_required": False},
                {"name": "Safety Leadership", "duration": "4 hours", "frequency": "annual", "osha_required": False},
                {"name": "Workers Compensation Management", "duration": "2 hours", "frequency": "annual", "osha_required": False},
            ],
            "construction": [
                {"name": "10-Hour OSHA Construction", "duration": "10 hours", "frequency": "once", "osha_required": True},
                {"name": "Fall Protection", "duration": "2 hours", "frequency": "annual", "osha_required": True},
                {"name": "Scaffold Safety", "duration": "1 hour", "frequency": "annual", "osha_required": True},
            ],
        }

        return {
            "role": role,
            "required_trainings": trainings.get(role, trainings["all_employees"]),
            "total_hours": sum(t["duration"].split()[0] for t in trainings.get(role, trainings["all_employees"]) if t["duration"].split()[0].isdigit()),
            "completion_status": {t["name"]: random.choice(["completed", "pending", "overdue"]) for t in trainings.get(role, trainings["all_employees"])},
        }

    def assess_ergonomics(self, assessment_data: Dict) -> Dict:
        """Assess workplace ergonomics"""
        work_type = assessment_data.get("work_type", "desk")
        hours_per_day = assessment_data.get("hours_per_day", 8)

        issues = []
        recommendations = []

        if work_type == "desk":
            issues.append({"area": "Monitor height", "score": 70, "recommendation": "Top of screen at eye level"})
            issues.append({"area": "Chair support", "score": 60, "recommendation": "Use lumbar support cushion"})
            issues.append({"area": "Keyboard position", "score": 75, "recommendation": "Elbows at 90 degrees"})
            recommendations.extend([
                "Take 2-minute break every 30 minutes",
                "Do 20-20-20 eye exercises every hour",
                "Stand and stretch every hour",
                "Use a sit-stand desk if possible",
            ])
        elif work_type == "manual":
            issues.append({"area": "Lifting technique", "score": 65, "recommendation": "Bend knees, keep back straight"})
            issues.append({"area": "PPE usage", "score": 80, "recommendation": "Ensure proper PPE at all times"})
            issues.append({"area": "Break frequency", "score": 70, "recommendation": "Take regular rest breaks"})
            recommendations.extend([
                "Use mechanical aids for heavy lifting",
                "Alternate tasks to avoid repetitive motions",
                "Wear appropriate PPE",
                "Stay hydrated",
            ])

        overall_score = sum(i["score"] for i in issues) / len(issues) if issues else 100

        return {
            "assessment_id": f"ERG-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "work_type": work_type,
            "hours_per_day": hours_per_day,
            "overall_score": round(overall_score),
            "issues": issues,
            "recommendations": recommendations,
            "risk_level": "low" if overall_score >= 80 else "medium" if overall_score >= 60 else "high",
            "reassessment_due": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d"),
        }


workplace_safety_service = WorkplaceSafetyService()
