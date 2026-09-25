"""
Categorized Technology & Specialization Extractor
Scans text with word boundaries and regex for high-precision extraction into structured categories.
"""

import re
from typing import Dict, List, Set, Tuple

# Categorized Knowledge Base
TECH_PATTERNS = {
    "programming_languages": [
        (r'\bpython\b', "Python"),
        (r'\bjava\b', "Java"),
        (r'\bjavascript\b', "JavaScript"),
        (r'\btypescript\b', "TypeScript"),
        (r'\bc\+\+\b', "C++"),
        (r'\bc#\b|\b\.net\b|\bdotnet\b', "C#"),
        (r'\bgolang\b|\bgo\s*(?:programming|lang|developer|engineer|backend)\b', "Go"),
        (r'\brust\b', "Rust"),
        (r'\bruby\b', "Ruby"),
        (r'\bphp\b', "PHP"),
        (r'\bscala\b', "Scala"),
        (r'\bkotlin\b', "Kotlin"),
        (r'\bswift\b', "Swift"),
        (r'\bobjective-c\b|\bobjc\b', "Objective-C"),
        (r'\bsql\b', "SQL"),
        (r'\bpl/sql\b', "PL/SQL"),
        (r'\bt-sql\b', "T-SQL"),
        (r'\br\b(?=\s*(?:programming|package|script|studio|developer))', "R"),
        (r'\bmatlab\b', "MATLAB"),
        (r'\bdart\b', "Dart"),
        (r'\blua\b', "Lua"),
        (r'\bperl\b', "Perl"),
        (r'\bbash\b', "Bash"),
        (r'\bshell\b', "Shell"),
        (r'\bpowershell\b', "PowerShell"),
        (r'\bsolidity\b', "Solidity"),
        (r'\bassembly\b', "Assembly"),
        (r'\bhlsl\b|\bglsl\b', "Shader Language")
    ],
    "frameworks": [
        (r'\breact(?:\.js|js)?\b', "React"),
        (r'\bangular(?:\.js|js)?\b', "Angular"),
        (r'\bvue(?:\.js|js)?\b', "Vue"),
        (r'\bsvelte\b', "Svelte"),
        (r'\bnext(?:\.js|js)?\b', "Next.js"),
        (r'\bnuxt(?:\.js|js)?\b', "Nuxt"),
        (r'\bnode(?:\.js|js)?\b', "Node.js"),
        (r'\bexpress(?:\.js|js)?\b', "Express"),
        (r'\bnest(?:\.js|js)?\b', "NestJS"),
        (r'\bfastapi\b', "FastAPI"),
        (r'\bdjango\b', "Django"),
        (r'\bflask\b', "Flask"),
        (r'\bspring\s*boot\b|\bspring\b', "Spring Boot"),
        (r'\bhibernate\b', "Hibernate"),
        (r'\bquarkus\b', "Quarkus"),
        (r'\bmicronaut\b', "Micronaut"),
        (r'\blaravel\b', "Laravel"),
        (r'\bsymfony\b', "Symfony"),
        (r'\bruby\s*on\s*rails\b|\brails\b', "Ruby on Rails"),
        (r'\basp\.net\b|\basp\.net\s*core\b', "ASP.NET Core"),
        (r'\btailwind\b', "Tailwind CSS"),
        (r'\bbootstrap\b', "Bootstrap"),
        (r'\bredux\b', "Redux"),
        (r'\brxjs\b', "RxJS"),
        (r'\bgraphql\b', "GraphQL"),
        (r'\bgrpc\b', "gRPC")
    ],
    "ai_ml": [
        (r'\bpytorch\b', "PyTorch"),
        (r'\btensorflow\b', "TensorFlow"),
        (r'\bkeras\b', "Keras"),
        (r'\bjax\b', "JAX"),
        (r'\bscikit-learn\b|\bsklearn\b', "scikit-learn"),
        (r'\bxgboost\b', "XGBoost"),
        (r'\blightgbm\b', "LightGBM"),
        (r'\bhugging\s*face\b|\btransformers\b', "Hugging Face"),
        (r'\blangchain\b', "LangChain"),
        (r'\bllamaindex\b', "LlamaIndex"),
        (r'\bmlflow\b', "MLflow"),
        (r'\bkubeflow\b', "Kubeflow"),
        (r'\bopencv\b', "OpenCV"),
        (r'\bonnx\b', "ONNX"),
        (r'\bspacy\b', "spaCy"),
        (r'\bnltk\b', "NLTK"),
        (r'\bopenai\s*api\b|\bopenai\b', "OpenAI"),
        (r'\bvllm\b', "vLLM"),
        (r'\btensorrt\b', "TensorRT"),
        (r'\bdeepspeed\b', "DeepSpeed")
    ],
    "cloud": [
        (r'\baws\b|\bamazon\s*web\s*services\b', "AWS"),
        (r'\bazure\b|\bmicrosoft\s*azure\b', "Azure"),
        (r'\bgcp\b|\bgoogle\s*cloud\b', "Google Cloud"),
        (r'\boracle\s*cloud\b', "Oracle Cloud"),
        (r'\bec2\b', "AWS EC2"),
        (r'\bs3\b', "AWS S3"),
        (r'\blambda\b', "AWS Lambda"),
        (r'\beks\b', "AWS EKS"),
        (r'\becs\b', "AWS ECS"),
        (r'\brds\b', "AWS RDS"),
        (r'\bdynamodb\b', "DynamoDB"),
        (r'\bcloudfront\b', "AWS CloudFront"),
        (r'\bapi\s*gateway\b', "API Gateway"),
        (r'\baks\b', "Azure AKS"),
        (r'\bazure\s*functions\b', "Azure Functions"),
        (r'\bgke\b', "GCP GKE"),
        (r'\bbigquery\b', "BigQuery"),
        (r'\bcloud\s*run\b', "Cloud Run")
    ],
    "containers_iac": [
        (r'\bdocker\b', "Docker"),
        (r'\bkubernetes\b|\bk8s\b', "Kubernetes"),
        (r'\bhelm\b', "Helm"),
        (r'\bterraform\b', "Terraform"),
        (r'\bpulumi\b', "Pulumi"),
        (r'\bansible\b', "Ansible"),
        (r'\bcloudformation\b', "CloudFormation"),
        (r'\bistio\b', "Istio"),
        (r'\bargo\s*cd\b|\bargo\b', "Argo CD")
    ],
    "ci_cd": [
        (r'\bjenkins\b', "Jenkins"),
        (r'\bgithub\s*actions\b', "GitHub Actions"),
        (r'\bgitlab\s*ci\b', "GitLab CI"),
        (r'\bcircleci\b', "CircleCI"),
        (r'\bazure\s*devops\b', "Azure DevOps"),
        (r'\bteamcity\b', "TeamCity"),
        (r'\bbamboo\b', "Bamboo")
    ],
    "databases": [
        (r'\bpostgresql\b|\bpostgres\b', "PostgreSQL"),
        (r'\bmysql\b', "MySQL"),
        (r'\bmariadb\b', "MariaDB"),
        (r'\boracle\s*database\b|\boracle\s*db\b', "Oracle DB"),
        (r'\bsql\s*server\b|\bmssql\b', "SQL Server"),
        (r'\bsqlite\b', "SQLite"),
        (r'\bmongodb\b|\bmongo\b', "MongoDB"),
        (r'\bcassandra\b', "Cassandra"),
        (r'\bcouchbase\b', "Couchbase"),
        (r'\bredis\b', "Redis"),
        (r'\belasticsearch\b|\belastic\b', "Elasticsearch"),
        (r'\bopensearch\b', "OpenSearch"),
        (r'\bneo4j\b', "Neo4j"),
        (r'\bsnowflake\b', "Snowflake"),
        (r'\bredshift\b', "Redshift"),
        (r'\bdatabricks\b', "Databricks"),
        (r'\bclickhouse\b', "ClickHouse")
    ],
    "messaging": [
        (r'\bkafka\b', "Kafka"),
        (r'\brabbitmq\b', "RabbitMQ"),
        (r'\bactivemq\b', "ActiveMQ"),
        (r'\baws\s*sqs\b|\bsqs\b', "AWS SQS"),
        (r'\baws\s*sns\b|\bsns\b', "AWS SNS"),
        (r'\bgoogle\s*pub/sub\b|\bpub/sub\b', "Google Pub/Sub")
    ],
    "monitoring": [
        (r'\bprometheus\b', "Prometheus"),
        (r'\bgrafana\b', "Grafana"),
        (r'\bdatadog\b', "Datadog"),
        (r'\bnew\s*relic\b', "New Relic"),
        (r'\bsplunk\b', "Splunk"),
        (r'\bopentelemetry\b|\botel\b', "OpenTelemetry")
    ],
    "security": [
        (r'\bokta\b', "Okta"),
        (r'\bauth0\b', "Auth0"),
        (r'\bcrowdstrike\b', "CrowdStrike"),
        (r'\bpalo\s*alto\b', "Palo Alto"),
        (r'\bfortinet\b', "Fortinet"),
        (r'\bburp\s*suite\b', "Burp Suite"),
        (r'\bmetasploit\b', "Metasploit"),
        (r'\bnmap\b', "Nmap"),
        (r'\bwireshark\b', "Wireshark"),
        (r'\bsnyk\b', "Snyk"),
        (r'\bsonarqube\b', "SonarQube"),
        (r'\bcheckmarx\b', "Checkmarx")
    ],
    "tools": [
        (r'\bgit\b|\bgithub\b|\bgitlab\b', "Git"),
        (r'\bjira\b', "Jira"),
        (r'\bconfluence\b', "Confluence"),
        (r'\bpostman\b', "Postman"),
        (r'\bfigma\b', "Figma")
    ]
}

SPECIALIZATION_PATTERNS = [
    (r'\bmicroservices\b', "Microservices"),
    (r'\bdistributed\s*systems\b', "Distributed Systems"),
    (r'\brest\s*api\b|\brestful\b', "REST API"),
    (r'\bgraphql\b', "GraphQL"),
    (r'\bevent\s*driven\b|\bevent-driven\b', "Event Driven Architecture"),
    (r'\breal[\s-]time\s*systems\b|\breal[\s-]time\s*data\b', "Real-Time Systems"),
    (r'\bhigh\s*performance\s*computing\b|\bhpc\b', "High Performance Computing"),
    (r'\blow\s*latency\b', "Low Latency"),
    (r'\bcloud\s*native\b', "Cloud Native"),
    (r'\bserverless\b', "Serverless"),
    (r'\bgenerative\s*ai\b|\bgenai\b', "Generative AI"),
    (r'\bllm\b|\blarge\s*language\s*models\b', "Large Language Models"),
    (r'\brag\b|\bretrieval\s*augmented\s*generation\b', "RAG"),
    (r'\bcomputer\s*vision\b', "Computer Vision"),
    (r'\bnlp\b|\bnatural\s*language\s*processing\b', "NLP"),
    (r'\bzero\s*trust\b', "Zero Trust"),
    (r'\biam\b|\bidentity\s*and\s*access\b', "IAM"),
    (r'\bdevsecops\b', "DevSecOps"),
    (r'\bmlops\b', "MLOps"),
    (r'\bdata\s*engineering\b', "Data Engineering"),
    (r'\bbig\s*data\b', "Big Data"),
    (r'\betl\b|\belt\b', "ETL"),
    (r'\bdata\s*warehousing\b', "Data Warehousing"),
    (r'\bbusiness\s*intelligence\b|\bbi\b', "Business Intelligence"),
    (r'\bmobile\b', "Mobile"),
    (r'\bembedded\b|\brtos\b', "Embedded"),
    (r'\biot\b|\binternet\s*of\s*things\b', "IoT"),
    (r'\bblockchain\b|\bweb3\b', "Blockchain / Web3"),
    (r'\bci/cd\b|\bcontinuous\s*integration\b', "CI/CD"),
    (r'\btest\s*automation\b|\be2e\s*testing\b', "Test Automation")
]


COMPILED_TECH_PATTERNS = {}
for _cat, _plist in TECH_PATTERNS.items():
    COMPILED_TECH_PATTERNS[_cat] = [(re.compile(p, re.IGNORECASE), name) for p, name in _plist]

COMPILED_SPEC_PATTERNS = [(re.compile(p, re.IGNORECASE), name) for p, name in SPECIALIZATION_PATTERNS]


def extract_technologies(text: str) -> Dict[str, List[str]]:
    """Extract categorized technologies from text"""
    if not text:
        return {cat: [] for cat in TECH_PATTERNS}
        
    results = {}
    for category, pattern_list in COMPILED_TECH_PATTERNS.items():
        found = []
        for p, canon_name in pattern_list:
            if p.search(text):
                if canon_name not in found:
                    found.append(canon_name)
        results[category] = found
        
    return results


def extract_specializations(text: str) -> List[str]:
    """Extract architectural and domain specializations from text"""
    if not text:
        return []
    found = []
    for p, name in COMPILED_SPEC_PATTERNS:
        if p.search(text):
            if name not in found:
                found.append(name)
    return found
