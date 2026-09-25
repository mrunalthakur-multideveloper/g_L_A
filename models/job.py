"""
Normalized Job Data Model
Represents a standardized job record across Greenhouse, Lever, and Ashby.
Preserves original raw descriptions verbatim while providing structured classification fields.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import json


@dataclass
class NormalizedJob:
    # Primary Identifiers
    id: str = ""
    job_id: str = ""
    source: str = ""  # "greenhouse" | "lever" | "ashby"
    
    # Core Job Metadata
    title: str = ""
    company_name: str = ""
    company_logo: Optional[str] = None
    company_url: Optional[str] = None
    department: Optional[str] = None
    job_type: Optional[str] = None
    job_level: Optional[str] = None  # Seniority
    company_industry: Optional[str] = None
    job_function: Optional[str] = None
    
    # Location
    location_display: str = ""
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    location_country: str = "USA"
    is_remote: bool = False
    is_easy_apply: bool = False
    
    # Dates
    date_posted: Optional[str] = None  # Original publication date (never overwritten)
    scraped_at: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
    
    # URLs
    job_url: str = ""
    apply_url: Optional[str] = None
    
    # Compensation
    compensation_min: Optional[float] = None
    compensation_max: Optional[float] = None
    compensation_currency: Optional[str] = "USD"
    compensation_interval: Optional[str] = "annual"
    salary_text: Optional[str] = None
    
    # Requirements & Auth
    experience: Optional[str] = None
    skills: List[str] = field(default_factory=list)
    sponsorship_h1b: str = "No"  # "Yes" | "No" | "Maybe"
    emails: List[str] = field(default_factory=list)
    search_keyword: Optional[str] = None
    
    # Undisturbed Descriptions
    description: str = ""          # Plain text description (preserved)
    description_html: Optional[str] = None  # Raw original HTML
    description_plain: Optional[str] = None # Raw original Plain Text
    
    # Classification Fields
    is_it_job: bool = False
    it_job_family: Optional[str] = None
    job_domain: Optional[str] = None       # Primary Domain
    job_domains: List[str] = field(default_factory=list)  # Secondary Domains
    classification_confidence: float = 0.0
    classification_method: str = "rules"  # "rules" | "ai_fallback" | "hybrid"
    classification_reason: str = ""
    
    # Categorized Technology Extraction
    technologies: Dict[str, List[str]] = field(default_factory=lambda: {
        "programming_languages": [],
        "frameworks": [],
        "ai_ml": [],
        "cloud": [],
        "containers_iac": [],
        "ci_cd": [],
        "databases": [],
        "messaging": [],
        "monitoring": [],
        "security": [],
        "tools": []
    })
    
    # Specializations
    specializations: List[str] = field(default_factory=list)
    
    # Platform-specific Raw Metadata
    raw_data: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for database insertion and CSV serialization"""
        data = asdict(self)
        # Ensure json string formatting for complex types when exported
        if isinstance(data.get("job_domains"), list):
            data["job_domains_json"] = json.dumps(data["job_domains"])
        if isinstance(data.get("technologies"), dict):
            data["technologies_json"] = json.dumps(data["technologies"])
        if isinstance(data.get("specializations"), list):
            data["specializations_json"] = json.dumps(data["specializations"])
        if isinstance(data.get("skills"), list):
            data["skills_json"] = json.dumps(data["skills"])
        if isinstance(data.get("emails"), list):
            data["emails_json"] = json.dumps(data["emails"])
        return data
