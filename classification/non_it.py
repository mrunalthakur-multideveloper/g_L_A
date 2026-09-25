"""
Non-IT Functional Domains Gate
Accurately detects whether a job's primary purpose is Non-IT across 30+ domains.
Prioritizes the actual ROLE/PURPOSE over incidental tool mentions (e.g. Python in Financial Analyst).
"""

import re
from typing import Tuple, List

# 30+ Non-IT Domain Patterns (Title / Department level)
NON_IT_DOMAINS = {
    "Healthcare & Clinical": [
        r'\bnurse\b', r'\bnursing\b', r'\bcna\b', r'\blpn\b', r'\brn\b', r'\bcaregiver\b',
        r'\bmedical\s*assistant\b', r'\bphlebotomist\b', r'\bphysician\b', r'\bdoctor\b',
        r'\btherapist\b', r'\bphysical\s*therapy\b', r'\boccupational\s*therapy\b',
        r'\bspeech\s*therapy\b', r'\bdental\b', r'\bhygienist\b', r'\bdentist\b',
        r'\bpatient\s*care\b', r'\bclinic\b', r'\bparamedic\b', r'\bemt\b',
        r'\bpharmacist\b', r'\bpharmacy\b', r'\bradiolog\w*', r'\bsurgical\b',
        r'\bclinical\s*coordinator\b', r'\bhealth\s*aide\b', r'\bcase\s*manager\b',
        r'\bveterinar\w*', r'\bvet\s*tech\b', r'\boptometrist\b', r'\bchiropractor\b'
    ],
    "Finance & Accounting": [
        r'\bfinancial\s*analyst\b', r'\baccountant\b', r'\baccounting\b', r'\bbookkeeper\b',
        r'\btax\s*analyst\b', r'\btax\s*specialist\b', r'\bauditor\b', r'\baudit\b',
        r'\bcontroller\b', r'\bpayroll\b', r'\bbilling\b', r'\baccounts\s*payable\b',
        r'\baccounts\s*receivable\b', r'\bunderwriter\b', r'\bactuary\b', r'\bactuarial\b',
        r'\bwealth\s*manager\b', r'\bfinancial\s*advisor\b', r'\bportfolio\s*manager\b',
        r'\bcredit\s*analyst\b', r'\bloan\s*officer\b', r'\bmortgage\b', r'\bteller\b'
    ],
    "HR & Recruiting": [
        r'\brecruiter\b', r'\btalent\s*acquisition\b', r'\bpeople\s*operations\b',
        r'\bpeople\s*partner\b', r'\bhr\s*generalist\b', r'\bhr\s*business\s*partner\b',
        r'\bhr\s*manager\b', r'\bhr\s*specialist\b', r'\bhuman\s*resources\b',
        r'\bcompensation\s*and\s*benefits\b', r'\btalent\s*partner\b', r'\bonboarding\b',
        r'\bemployee\s*relations\b', r'\bheadhunter\b'
    ],
    "Sales & Business Development": [
        r'\baccount\s*executive\b', r'\bsales\s*representative\b', r'\bsales\s*manager\b',
        r'\bsales\s*director\b', r'\bbusiness\s*development\s*rep\w*\b', r'\bbdr\b', r'\bsdr\b',
        r'\binside\s*sales\b', r'\boutside\s*sales\b', r'\bterritory\s*manager\b',
        r'\bcommercial\s*executive\b', r'\bsales\s*consultant\b'
    ],
    "Marketing & Growth": [
        r'\bmarketing\s*manager\b', r'\bmarketing\s*specialist\b', r'\bmarketing\s*director\b',
        r'\bcontent\s*writer\b', r'\bcopywriter\b', r'\bseo\s*specialist\b',
        r'\bsocial\s*media\s*manager\b', r'\bbrand\s*manager\b', r'\bpublic\s*relations\b',
        r'\bpr\s*manager\b', r'\bcommunications\s*manager\b', r'\bevent\s*planner\b',
        r'\bmedia\s*planner\b', r'\bemail\s*marketer\b', r'\bdigital\s*marketer\b'
    ],
    "Customer Support & Success": [
        r'\bcustomer\s*service\s*rep\w*\b', r'\bcustomer\s*support\s*specialist\b',
        r'\bcall\s*center\s*agent\b', r'\bcustomer\s*care\b', r'\bclient\s*services\b',
        r'\bcustomer\s*advocate\b', r'\bhelpdesk\s*agent\b'
    ],
    "Legal & Compliance": [
        r'\battorney\b', r'\blawyer\b', r'\bcounsel\b', r'\bparalegal\b',
        r'\blegal\s*assistant\b', r'\bcontract\s*manager\b', r'\bcompliance\s*officer\b',
        r'\bregulatory\s*affairs\b', r'\blegal\s*counsel\b'
    ],
    "Logistics, Warehouse & Trades": [
        r'\bdriver\b', r'\btruck\s*driver\b', r'\bcdl\b', r'\bwarehouse\s*associate\b',
        r'\bwarehouse\s*worker\b', r'\bforklift\b', r'\bdelivery\b', r'\bcourier\b',
        r'\bloader\b', r'\bunloader\b', r'\bpacker\b', r'\bmover\b', r'\bcustodian\b',
        r'\bjanitor\b', r'\bcleaner\b', r'\bhousekeeper\b', r'\bhousekeeping\b',
        r'\blandscaper\b', r'\bplumber\b', r'\belectrician\b', r'\bcarpenter\b',
        r'\bwelder\b', r'\bhvac\b', r'\bmechanic\b', r'\bfacilities\s*technician\b',
        r'\bmaintenance\s*tech\w*\b'
    ],
    "Hospitality, Culinary & Retail": [
        r'\bcook\b', r'\bchef\b', r'\bbarista\b', r'\bcashier\b', r'\bwaiter\b',
        r'\bwaitress\b', r'\bserver\b', r'\bdishwasher\b', r'\bculinary\b',
        r'\brestaurant\b', r'\bbartender\b', r'\bfood\s*prep\b', r'\bhostess\b',
        r'\bhotel\b', r'\bstore\s*associate\b', r'\bretail\s*associate\b',
        r'\bmerchandiser\b', r'\bstocker\b'
    ],
    "Traditional Engineering (Non-Software)": [
        r'\bmechanical\s*engineer\b', r'\bcivil\s*engineer\b', r'\bchemical\s*engineer\b',
        r'\bstructural\s*engineer\b', r'\bpetroleum\s*engineer\b', r'\baerospace\s*engineer\b',
        r'\bmaterials\s*engineer\b', r'\benvironmental\s*engineer\b', r'\bprocess\s*engineer\b',
        r'\bmanufacturing\s*engineer\b', r'\bindustrial\s*engineer\b', r'\bquality\s*inspector\b'
    ],
    "Administration & Clerical": [
        r'\breceptionist\b', r'\bfront\s*desk\b', r'\badministrative\s*assistant\b',
        r'\boffice\s*assistant\b', r'\bexecutive\s*assistant\b', r'\boffice\s*manager\b',
        r'\bclerk\b', r'\bdata\s*entry\b'
    ],
    "Real Estate & Property": [
        r'\breal\s*estate\s*agent\b', r'\bleasing\s*agent\b', r'\bproperty\s*manager\b',
        r'\bleasing\s*consultant\b', r'\brealtor\b'
    ],
    "Education & Childcare": [
        r'\bteacher\b', r'\btutor\b', r'\bdaycare\b', r'\bnanny\b',
        r'\bkindergarten\b', r'\belementary\s*teacher\b', r'\bprofessor\s*of\s*(?!computer|software|data|ai)',
        r'\binstructor\s*of\s*(?!computer|software|data|ai)'
    ],
    "Physical Security": [
        r'\bsecurity\s*guard\b', r'\bpatrol\s*officer\b', r'\bloss\s*prevention\b'
    ]
}

# Strong IT Affirmative Roles that override accidental sub-matches
STRONG_IT_OVERRIDES = [
    r'\bsoftware\b', r'\bdeveloper\b', r'\bfullstack\b', r'\bfull-stack\b',
    r'\bfrontend\b', r'\bfront-end\b', r'\bbackend\b', r'\bback-end\b',
    r'\bmachine\s*learning\b', r'\bdata\s*scientist\b', r'\bdata\s*engineer\b',
    r'\bdevops\b', r'\bsre\b', r'\bsite\s*reliability\b', r'\bcloud\s*engineer\b',
    r'\bcybersecurity\b', r'\binformation\s*security\b', r'\bsecurity\s*engineer\b',
    r'\bsdet\b', r'\bqa\s*automation\b', r'\btech\s*lead\b', r'\barchitect\b',
    r'\bproduct\s*manager\b', r'\bproduct\s*management\b', r'\bdatabase\s*administrator\b',
    r'\bfirmware\s*engineer\b', r'\bembedded\s*software\b', r'\bweb\s*developer\b',
    r'\bios\s*developer\b', r'\bandroid\s*developer\b', r'\bplatform\s*engineer\b',
    r'\bnetwork\s*engineer\b', r'\bsystems\s*engineer\b', r'\btechnical\s*sourcer\b'
]

COMPILED_IT_OVERRIDES = [re.compile(p, re.IGNORECASE) for p in STRONG_IT_OVERRIDES]

COMPILED_NON_IT_DOMAINS = {}
for _domain, _patterns in NON_IT_DOMAINS.items():
    COMPILED_NON_IT_DOMAINS[_domain] = [re.compile(p, re.IGNORECASE) for p in _patterns]


def evaluate_non_it_purpose(job_title: str, department: str = "", description: str = "") -> Tuple[bool, str]:
    """
    Evaluates whether the job's primary purpose is Non-IT.
    Returns: (is_non_it: bool, matched_reason: str)
    """
    if not job_title:
        return True, "Missing job title"
        
    title_clean = job_title.strip()
    dept_clean = str(department).strip() if department else ""
    
    # 1. Check strong IT overrides first (e.g. "Software Engineer, Healthcare" -> IT)
    for p in COMPILED_IT_OVERRIDES:
        if p.search(title_clean):
            return False, f"Strong IT role identified: {p.pattern}"

    # 2. Check for Non-IT Title / Department matches
    for domain_name, patterns in COMPILED_NON_IT_DOMAINS.items():
        for p in patterns:
            if p.search(title_clean):
                return True, f"Non-IT {domain_name} role: title matched '{p.pattern}'"
            if dept_clean and p.search(dept_clean):
                # Only if title has no tech markers
                if not any(override.search(title_clean) for override in COMPILED_IT_OVERRIDES):
                    return True, f"Non-IT {domain_name} department: dept matched '{p.pattern}'"
                    
    return False, "Not matched by Non-IT filters"
