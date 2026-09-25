"""
IT Job Classification Taxonomy
Contains definitions for 24+ IT Job Families and 60+ Primary Domains with comprehensive aliases,
associated languages, frameworks, libraries, databases, and architectural specializations.
"""

IT_JOB_TAXONOMY = {
    # ── 1. SOFTWARE ENGINEERING ─────────────────────────────────────
    "Software Engineer": {
        "family": "Software Engineering",
        "titles": [
            r"\bsoftware\s*engineer\b", r"\bsoftware\s*developer\b", r"\bapplication\s*engineer\b",
            r"\bapplication\s*developer\b", r"\bprogrammer\b", r"\bswe\b", r"\bcore\s*engineer\b"
        ],
        "languages": ["Python", "Java", "C++", "C#", "Go", "Rust", "TypeScript", "JavaScript"],
        "frameworks": [],
        "specializations": ["Software Architecture", "Clean Code", "Design Patterns", "Algorithms"]
    },
    "Backend Developer": {
        "family": "Software Engineering",
        "titles": [
            r"\bbackend\s*engineer\b", r"\bbackend\s*developer\b", r"\bback-end\s*engineer\b",
            r"\bback\s*end\s*developer\b", r"\bserver-side\s*engineer\b", r"\bapi\s*engineer\b",
            r"\bapi\s*developer\b", r"\bservices\s*engineer\b"
        ],
        "languages": ["Python", "Java", "Go", "Rust", "C#", "Node.js", "Ruby", "PHP", "Scala"],
        "frameworks": ["Spring Boot", "FastAPI", "Django", "Express", "NestJS", "ASP.NET", "Rails"],
        "specializations": ["REST API", "GraphQL", "Microservices", "gRPC", "Distributed Systems"]
    },
    "Frontend Developer": {
        "family": "Software Engineering",
        "titles": [
            r"\bfrontend\s*engineer\b", r"\bfrontend\s*developer\b", r"\bfront-end\s*engineer\b",
            r"\bfront\s*end\s*developer\b", r"\bweb\s*developer\b", r"\bui\s*engineer\b", r"\bclient\s*engineer\b"
        ],
        "languages": ["JavaScript", "TypeScript", "HTML", "CSS"],
        "frameworks": ["React", "Angular", "Vue", "Next.js", "Svelte", "Nuxt", "Tailwind", "Bootstrap"],
        "specializations": ["UI/UX", "Single Page Applications", "Web Performance", "State Management"]
    },
    "Full Stack Developer": {
        "family": "Software Engineering",
        "titles": [
            r"\bfullstack\s*engineer\b", r"\bfullstack\s*developer\b", r"\bfull-stack\s*engineer\b",
            r"\bfull\s*stack\s*developer\b", r"\bfull\s*stack\s*software\s*engineer\b"
        ],
        "languages": ["JavaScript", "TypeScript", "Python", "Java", "C#", "Go"],
        "frameworks": ["React", "Node.js", "Spring Boot", "Next.js", "Angular", "Vue", "Django"],
        "specializations": ["End-to-End Development", "Full Lifecycle", "API Integration", "Database Design"]
    },
    "Java Developer": {
        "family": "Software Engineering",
        "titles": [
            r"\bjava\s*developer\b", r"\bjava\s*engineer\b", r"\bjava\s*software\s*engineer\b",
            r"\bjava\s*backend\s*developer\b", r"\bjava\s*backend\s*engineer\b", r"\bjava\s*backend\b",
            r"\bjava\s*fullstack\s*engineer\b", r"\bcore\s*java\s*developer\b"
        ],
        "languages": ["Java"],
        "frameworks": ["Spring", "Spring Boot", "Hibernate", "Quarkus", "Micronaut", "JPA"],
        "specializations": ["Enterprise Java", "JVM Optimization", "Microservices", "Spring Security"]
    },
    "Python Developer": {
        "family": "Software Engineering",
        "titles": [
            r"\bpython\s*developer\b", r"\bpython\s*engineer\b", r"\bpython\s*software\s*engineer\b",
            r"\bpython\s*backend\s*engineer\b", r"\bpython\s*backend\s*developer\b", r"\bpython\s*backend\b",
            r"\bpython\s*fullstack\s*engineer\b"
        ],
        "languages": ["Python"],
        "frameworks": ["FastAPI", "Django", "Flask", "Celery", "Pydantic", "SQLAlchemy"],
        "specializations": ["AsyncIO", "API Development", "Scripting & Automation", "Microservices"]
    },
    "JavaScript Developer": {
        "family": "Software Engineering",
        "titles": [
            r"\bjavascript\s*developer\b", r"\bjavascript\s*engineer\b", r"\bjs\s*developer\b"
        ],
        "languages": ["JavaScript"],
        "frameworks": ["Node.js", "Express", "React", "Vue"],
        "specializations": ["ES6+", "Asynchronous Programming", "Event Loop"]
    },
    "TypeScript Developer": {
        "family": "Software Engineering",
        "titles": [
            r"\btypescript\s*developer\b", r"\btypescript\s*engineer\b", r"\bts\s*developer\b"
        ],
        "languages": ["TypeScript"],
        "frameworks": ["React", "NestJS", "Next.js", "Node.js"],
        "specializations": ["Type Systems", "Generics", "Frontend/Backend TS"]
    },
    "React Developer": {
        "family": "Software Engineering",
        "titles": [
            r"\breact\s*developer\b", r"\breact\s*engineer\b", r"\breact\.js\s*developer\b",
            r"\breactjs\s*developer\b", r"\breact\s*frontend\s*engineer\b"
        ],
        "languages": ["JavaScript", "TypeScript"],
        "frameworks": ["React", "Next.js", "Redux", "Zustand", "Tailwind"],
        "specializations": ["React Hooks", "SSR", "Client Side Rendering"]
    },
    "Angular Developer": {
        "family": "Software Engineering",
        "titles": [
            r"\bangular\s*developer\b", r"\bangular\s*engineer\b", r"\bangularjs\s*developer\b"
        ],
        "languages": ["TypeScript", "JavaScript"],
        "frameworks": ["Angular", "RxJS", "NgRx"],
        "specializations": ["Component Architecture", "Dependency Injection", "Reactive Forms"]
    },
    "Vue Developer": {
        "family": "Software Engineering",
        "titles": [
            r"\bvue\s*developer\b", r"\bvue\s*engineer\b", r"\bvue\.js\s*developer\b", r"\bvuejs\s*developer\b"
        ],
        "languages": ["JavaScript", "TypeScript"],
        "frameworks": ["Vue", "Nuxt", "Pinia", "Vuex"],
        "specializations": ["Composition API", "SFC", "Reactivity"]
    },
    "Node.js Developer": {
        "family": "Software Engineering",
        "titles": [
            r"\bnode\s*developer\b", r"\bnode\.js\s*developer\b", r"\bnodejs\s*engineer\b", r"\bnode\s*backend\s*engineer\b"
        ],
        "languages": ["JavaScript", "TypeScript"],
        "frameworks": ["Node.js", "Express", "NestJS", "Fastify"],
        "specializations": ["Event-Driven", "REST APIs", "WebSockets"]
    },
    "C++ Developer": {
        "family": "Software Engineering",
        "titles": [
            r"\bc\+\+\s*developer\b", r"\bc\+\+\s*engineer\b", r"\bcpp\s*developer\b", r"\bc\s*/\s*c\+\+\s*engineer\b"
        ],
        "languages": ["C++", "C"],
        "frameworks": ["Boost", "Qt", "STL"],
        "specializations": ["Memory Management", "High Performance Computing", "Low Latency", "Multi-threading"]
    },
    "C#/.NET Developer": {
        "family": "Software Engineering",
        "titles": [
            r"\bc#\s*developer\b", r"\bc#\s*engineer\b", r"\b\.net\s*developer\b",
            r"\bdotnet\s*developer\b", r"\b\.net\s*core\s*engineer\b", r"\basp\.net\s*developer\b"
        ],
        "languages": ["C#"],
        "frameworks": [".NET", ".NET Core", "ASP.NET", "Entity Framework", "WPF"],
        "specializations": ["Enterprise Architecture", "C# Async", "LINQ", "Microservices"]
    },
    "Go Developer": {
        "family": "Software Engineering",
        "titles": [
            r"\bgo\s*developer\b", r"\bgo\s*engineer\b", r"\bgolang\s*developer\b", r"\bgolang\s*engineer\b"
        ],
        "languages": ["Go"],
        "frameworks": ["Gin", "Echo", "Fiber", "gRPC"],
        "specializations": ["Concurrency & Goroutines", "Microservices", "Distributed Systems"]
    },
    "Rust Developer": {
        "family": "Software Engineering",
        "titles": [
            r"\brust\s*developer\b", r"\brust\s*engineer\b", r"\brust\s*systems\s*engineer\b"
        ],
        "languages": ["Rust"],
        "frameworks": ["Tokio", "Actix", "Axum"],
        "specializations": ["Memory Safety", "Systems Programming", "Concurrency", "High Performance"]
    },
    "Ruby Developer": {
        "family": "Software Engineering",
        "titles": [
            r"\bruby\s*developer\b", r"\bruby\s*engineer\b", r"\brails\s*developer\b", r"\bruby\s*on\s*rails\s*developer\b"
        ],
        "languages": ["Ruby"],
        "frameworks": ["Ruby on Rails", "Sinatra", "Sidekiq"],
        "specializations": ["MVC", "ActiveRecord", "Metaprogramming"]
    },
    "PHP Developer": {
        "family": "Software Engineering",
        "titles": [
            r"\bphp\s*developer\b", r"\bphp\s*engineer\b", r"\blaravel\s*developer\b", r"\bsymfony\s*developer\b"
        ],
        "languages": ["PHP"],
        "frameworks": ["Laravel", "Symfony", "WordPress", "Drupal"],
        "specializations": ["Web Application Development", "Eloquent ORM"]
    },
    "Scala Developer": {
        "family": "Software Engineering",
        "titles": [
            r"\bscala\s*developer\b", r"\bscala\s*engineer\b", r"\bscala\s*backend\s*engineer\b"
        ],
        "languages": ["Scala", "Java"],
        "frameworks": ["Akka", "Play", "Spark", "Cats"],
        "specializations": ["Functional Programming", "Distributed Computing", "Actor Model"]
    },
    "Distributed Systems Engineer": {
        "family": "Software Engineering",
        "titles": [
            r"\bdistributed\s*systems\s*engineer\b", r"\bdistributed\s*systems\s*developer\b",
            r"\bdistributed\s*computing\s*engineer\b", r"\bbackend\s*distributed\s*systems\b"
        ],
        "languages": ["Go", "Rust", "C++", "Java"],
        "frameworks": ["gRPC", "Kafka", "Raft", "Consul"],
        "specializations": ["Consensus Algorithms", "High Availability", "Fault Tolerance", "Scalability"]
    },
    "Software Architect": {
        "family": "Architecture",
        "titles": [
            r"\bsoftware\s*architect\b", r"\bsolutions\s*architect\b", r"\benterprise\s*architect\b",
            r"\bprincipal\s*architect\b", r"\btechnical\s*architect\b", r"\bsystem\s*architect\b"
        ],
        "languages": [],
        "frameworks": [],
        "specializations": ["System Design", "Cloud Architecture", "Scalability", "Domain-Driven Design"]
    },

    # ── 2. AI & MACHINE LEARNING ────────────────────────────────────
    "Machine Learning Engineer": {
        "family": "AI / Machine Learning",
        "titles": [
            r"\bmachine\s*learning\s*engineer\b", r"\bml\s*engineer\b", r"\bapplied\s*ml\s*engineer\b",
            r"\bml\s*systems\s*engineer\b", r"\bmachine\s*learning\s*developer\b"
        ],
        "languages": ["Python", "C++", "R"],
        "frameworks": ["PyTorch", "TensorFlow", "scikit-learn", "Keras", "XGBoost", "MLflow"],
        "specializations": ["Model Training", "Inference Optimization", "Feature Engineering", "ML Pipelines"]
    },
    "AI Engineer": {
        "family": "AI / Machine Learning",
        "titles": [
            r"\bai\s*engineer\b", r"\bartificial\s*intelligence\s*engineer\b", r"\bai\s*software\s*engineer\b",
            r"\bai\s*application\s*developer\b", r"\bai\s*systems\s*engineer\b"
        ],
        "languages": ["Python", "TypeScript"],
        "frameworks": ["LangChain", "LlamaIndex", "OpenAI", "Hugging Face", "PyTorch"],
        "specializations": ["Generative AI", "AI Agents", "LLM Integration", "Prompt Engineering"]
    },
    "Generative AI / LLM Engineer": {
        "family": "AI / Machine Learning",
        "titles": [
            r"\bgenerative\s*ai\s*engineer\b", r"\bllm\s*engineer\b", r"\bgenai\s*engineer\b",
            r"\bprompt\s*engineer\b", r"\brag\s*engineer\b", r"\bllm\s*developer\b"
        ],
        "languages": ["Python"],
        "frameworks": ["Transformers", "Hugging Face", "LangChain", "LlamaIndex", "vLLM"],
        "specializations": ["RAG", "Fine Tuning", "Vector Search", "Embeddings", "AI Agents"]
    },
    "Deep Learning / NLP / Computer Vision Engineer": {
        "family": "AI / Machine Learning",
        "titles": [
            r"\bdeep\s*learning\s*engineer\b", r"\bnlp\s*engineer\b", r"\bcomputer\s*vision\s*engineer\b",
            r"\bspeech\s*ai\s*engineer\b", r"\bcv\s*engineer\b"
        ],
        "languages": ["Python", "C++"],
        "frameworks": ["PyTorch", "OpenCV", "Transformers", "spaCy", "NLTK"],
        "specializations": ["Object Detection", "Transformers", "Semantic Segmentation", "ASR"]
    },
    "MLOps Engineer": {
        "family": "AI / Machine Learning",
        "titles": [
            r"\bmlops\s*engineer\b", r"\bmachine\s*learning\s*ops\s*engineer\b", r"\bai\s*platform\s*engineer\b",
            r"\bml\s*infrastructure\s*engineer\b"
        ],
        "languages": ["Python", "Bash"],
        "frameworks": ["Kubeflow", "MLflow", "Triton", "Ray", "Docker", "Kubernetes"],
        "specializations": ["Model Deployment", "Model Monitoring", "ML Pipelines", "GPU Orchestration"]
    },
    "Research Scientist": {
        "family": "AI / Machine Learning",
        "titles": [
            r"\bresearch\s*scientist\b", r"\bapplied\s*scientist\b", r"\bai\s*researcher\b",
            r"\bmachine\s*learning\s*researcher\b", r"\bpostdoctoral\s*researcher\b"
        ],
        "languages": ["Python", "R", "C++"],
        "frameworks": ["PyTorch", "JAX", "NumPy"],
        "specializations": ["Algorithm Innovation", "Peer Review", "Theoretical ML", "Experimental Design"]
    },

    # ── 3. DATA & ANALYTICS ─────────────────────────────────────────
    "Data Scientist": {
        "family": "Data",
        "titles": [
            r"\bdata\s*scientist\b", r"\bapplied\s*data\s*scientist\b", r"\blead\s*data\s*scientist\b",
            r"\bprincipal\s*data\s*scientist\b", r"\bquantitative\s*researcher\b"
        ],
        "languages": ["Python", "R", "SQL"],
        "frameworks": ["pandas", "NumPy", "scikit-learn", "statsmodels", "SciPy"],
        "specializations": ["Statistical Analysis", "Predictive Modeling", "A/B Testing", "Hypothesis Testing"]
    },
    "Data Engineer": {
        "family": "Data",
        "titles": [
            r"\bdata\s*engineer\b", r"\bbig\s*data\s*engineer\b", r"\betl\s*developer\b",
            r"\bdata\s*pipeline\s*engineer\b", r"\banalytics\s*engineer\b", r"\bdata\s*warehouse\s*engineer\b"
        ],
        "languages": ["Python", "SQL", "Scala", "Java"],
        "frameworks": ["Spark", "Airflow", "dbt", "Kafka", "Flink", "Snowflake", "Databricks"],
        "specializations": ["ETL/ELT", "Data Warehousing", "Stream Processing", "Data Modeling"]
    },
    "Data Analyst / BI Developer": {
        "family": "Business Intelligence",
        "titles": [
            r"\bdata\s*analyst\b", r"\bbi\s*developer\b", r"\bbi\s*engineer\b",
            r"\bbusiness\s*intelligence\s*analyst\b", r"\btableau\s*developer\b", r"\bpower\s*bi\s*developer\b"
        ],
        "languages": ["SQL", "Python", "R"],
        "frameworks": ["Tableau", "Power BI", "Looker", "Metabase", "dbt"],
        "specializations": ["Dashboards", "Data Visualization", "Ad-hoc SQL Analysis", "KPI Reporting"]
    },
    "Database Engineer / DBA": {
        "family": "Database",
        "titles": [
            r"\bdatabase\s*engineer\b", r"\bdatabase\s*administrator\b", r"\bdba\b",
            r"\bdatabase\s*architect\b", r"\bsql\s*developer\b", r"\bpostgres\s*dba\b"
        ],
        "languages": ["SQL", "PL/SQL", "T-SQL", "Bash"],
        "frameworks": ["PostgreSQL", "MySQL", "Oracle", "SQL Server", "MongoDB", "Redis"],
        "specializations": ["Query Optimization", "Database Replication", "Backup & Recovery", "Indexing"]
    },

    # ── 4. CLOUD, DEVOPS & INFRASTRUCTURE ───────────────────────────
    "DevOps Engineer": {
        "family": "DevOps",
        "titles": [
            r"\bdevops\s*engineer\b", r"\bdevops\s*architect\b", r"\bdevops\s*specialist\b",
            r"\bci/cd\s*engineer\b", r"\brelease\s*engineer\b", r"\bbuild\s*engineer\b"
        ],
        "languages": ["Bash", "Python", "Go", "YAML"],
        "frameworks": ["Terraform", "Docker", "Kubernetes", "Jenkins", "GitHub Actions", "Ansible", "Argo CD"],
        "specializations": ["CI/CD Automation", "Infrastructure as Code", "Containerization", "Release Management"]
    },
    "Cloud Engineer": {
        "family": "Cloud / Infrastructure",
        "titles": [
            r"\bcloud\s*engineer\b", r"\bcloud\s*architect\b", r"\bcloud\s*infrastructure\s*engineer\b",
            r"\baws\s*engineer\b", r"\bazure\s*cloud\s*engineer\b", r"\bgcp\s*engineer\b"
        ],
        "languages": ["Python", "Terraform", "Bash"],
        "frameworks": ["AWS", "Azure", "Google Cloud", "Terraform", "CloudFormation"],
        "specializations": ["Cloud Migration", "Multi-Cloud", "Cost Optimization", "Serverless"]
    },
    "Site Reliability Engineer (SRE)": {
        "family": "Site Reliability",
        "titles": [
            r"\bsite\s*reliability\s*engineer\b", r"\bsre\b", r"\bproduction\s*engineer\b",
            r"\breliability\s*engineer\b", r"\bprincipal\s*sre\b"
        ],
        "languages": ["Go", "Python", "Bash"],
        "frameworks": ["Prometheus", "Grafana", "Datadog", "Kubernetes", "OpenTelemetry"],
        "specializations": ["SLOs/SLAs", "Incident Response", "Chaos Engineering", "Observability", "Capacity Planning"]
    },
    "Platform / Infrastructure Engineer": {
        "family": "Platform Engineering",
        "titles": [
            r"\bplatform\s*engineer\b", r"\binfrastructure\s*engineer\b", r"\bcloud\s*platform\s*engineer\b",
            r"\bdeveloper\s*experience\s*engineer\b", r"\bdeveloper\s*productivity\s*engineer\b"
        ],
        "languages": ["Go", "Python", "Rust"],
        "frameworks": ["Kubernetes", "Terraform", "Backstage", "Docker", "Helm"],
        "specializations": ["Internal Developer Platforms", "Core Infrastructure", "Tooling Automation"]
    },

    # ── 5. CYBERSECURITY ────────────────────────────────────────────
    "Cybersecurity Engineer": {
        "family": "Cybersecurity",
        "titles": [
            r"\bsecurity\s*engineer\b", r"\bcybersecurity\s*engineer\b", r"\binformation\s*security\s*engineer\b",
            r"\bapplication\s*security\s*engineer\b", r"\bappsec\s*engineer\b", r"\bcloud\s*security\s*engineer\b",
            r"\bsecurity\s*architect\b", r"\binfosec\s*engineer\b", r"\bdevsecops\s*engineer\b"
        ],
        "languages": ["Python", "Bash", "Go", "C"],
        "frameworks": ["Okta", "Snyk", "SonarQube", "CrowdStrike", "Wiz", "Burp Suite"],
        "specializations": ["Application Security", "Threat Modeling", "Vulnerability Assessment", "Zero Trust", "IAM"]
    },
    "SOC Analyst / Security Analyst": {
        "family": "Cybersecurity",
        "titles": [
            r"\bsoc\s*analyst\b", r"\bsecurity\s*analyst\b", r"\bcybersecurity\s*analyst\b",
            r"\bincident\s*response\s*engineer\b", r"\bthreat\s*intel\s*analyst\b", r"\bpenetration\s*tester\b"
        ],
        "languages": ["Python", "SQL", "Bash"],
        "frameworks": ["Splunk", "SIEM", "Wireshark", "Metasploit", "Nmap"],
        "specializations": ["Incident Handling", "Penetration Testing", "Threat Hunting", "Forensics"]
    },

    # ── 6. QA & TESTING ─────────────────────────────────────────────
    "QA / SDET Engineer": {
        "family": "QA / Testing",
        "titles": [
            r"\bqa\s*engineer\b", r"\bqa\s*automation\s*engineer\b", r"\btest\s*automation\s*engineer\b",
            r"\bsdet\b", r"\bsoftware\s*development\s*engineer\s*in\s*test\b", r"\bquality\s*assurance\s*engineer\b",
            r"\bsoftware\s*test\s*engineer\b", r"\bperformance\s*test\s*engineer\b"
        ],
        "languages": ["Python", "Java", "JavaScript", "TypeScript"],
        "frameworks": ["Selenium", "Playwright", "Cypress", "PyTest", "JUnit", "JMeter", "Postman"],
        "specializations": ["E2E Automation", "API Testing", "Load & Performance Testing", "Regression Testing"]
    },

    # ── 7. MOBILE DEVELOPMENT ───────────────────────────────────────
    "Mobile Developer (iOS / Android)": {
        "family": "Mobile Development",
        "titles": [
            r"\bmobile\s*engineer\b", r"\bmobile\s*developer\b", r"\bios\s*engineer\b", r"\bios\s*developer\b",
            r"\bandroid\s*engineer\b", r"\bandroid\s*developer\b", r"\breact\s*native\s*engineer\b",
            r"\bflutter\s*developer\b", r"\bflutter\s*engineer\b"
        ],
        "languages": ["Swift", "Kotlin", "Java", "Objective-C", "Dart", "TypeScript"],
        "frameworks": ["SwiftUI", "UIKit", "Jetpack Compose", "React Native", "Flutter"],
        "specializations": ["App Store Release", "Mobile UI", "Offline Storage", "Mobile Performance"]
    },

    # ── 8. EMBEDDED, HARDWARE & ROBOTICS ───────────────────────────
    "Embedded / Firmware Engineer": {
        "family": "Embedded Systems",
        "titles": [
            r"\bembedded\s*software\s*engineer\b", r"\bembedded\s*engineer\b", r"\bfirmware\s*engineer\b",
            r"\bfirmware\s*developer\b", r"\brobotics\s*software\s*engineer\b", r"\biot\s*engineer\b",
            r"\bdevice\s*driver\s*engineer\b", r"\bhw/sw\s*engineer\b"
        ],
        "languages": ["C", "C++", "Rust", "Assembly", "Python"],
        "frameworks": ["FreeRTOS", "Linux Kernel", "ROS", "ROS 2", "ESP-IDF"],
        "specializations": ["RTOS", "Microcontrollers (ARM/STM32)", "Device Drivers", "Hardware Protocols (I2C/SPI/CAN)"]
    },

    # ── 9. BLOCKCHAIN & WEB3 ────────────────────────────────────────
    "Blockchain / Web3 Developer": {
        "family": "Blockchain / Web3",
        "titles": [
            r"\bblockchain\s*developer\b", r"\bblockchain\s*engineer\b", r"\bweb3\s*developer\b",
            r"\bsmart\s*contract\s*engineer\b", r"\bsolidity\s*developer\b", r"\bcrypto\s*engineer\b"
        ],
        "languages": ["Solidity", "Rust", "Go", "JavaScript"],
        "frameworks": ["Hardhat", "Foundry", "Ethers.js", "Web3.js"],
        "specializations": ["Smart Contracts", "DeFi", "EVM", "Tokenomics", "Consensus"]
    },

    # ── 10. GAME DEVELOPMENT ────────────────────────────────────────
    "Game Developer": {
        "family": "Game Development",
        "titles": [
            r"\bgame\s*developer\b", r"\bgame\s*engineer\b", r"\bgameplay\s*programmer\b",
            r"\bgraphics\s*programmer\b", r"\bgame\s*engine\s*engineer\b", r"\brendering\s*engineer\b"
        ],
        "languages": ["C++", "C#", "HLSL", "GLSL"],
        "frameworks": ["Unreal Engine", "Unity", "DirectX", "OpenGL", "Vulkan"],
        "specializations": ["Game Physics", "3D Rendering", "Shader Programming", "Animation Systems"]
    },

    # ── 11. NETWORKING ──────────────────────────────────────────────
    "Network Engineer": {
        "family": "Networking",
        "titles": [
            r"\bnetwork\s*engineer\b", r"\bnetwork\s*administrator\b", r"\bnetwork\s*architect\b",
            r"\bnetwork\s*security\s*engineer\b", r"\bcloud\s*network\s*engineer\b"
        ],
        "languages": ["Python", "Bash"],
        "frameworks": ["Cisco", "Juniper", "Arista", "BGP", "OSPF", "VPC"],
        "specializations": ["Routing & Switching", "SDN", "Network Automation", "Firewalls"]
    },

    # ── 12. TECHNICAL PRODUCT & PROGRAM ─────────────────────────────
    "Technical Product / Program Manager": {
        "family": "Technical Product / Program",
        "titles": [
            r"\btechnical\s*product\s*manager\b", r"\btpm\b", r"\btechnical\s*program\s*manager\b",
            r"\bproduct\s*manager\s*-\s*technical\b", r"\bproduct\s*manager\s*-\s*platform\b",
            r"\bproduct\s*manager\s*-\s*infrastructure\b", r"\bproduct\s*owner\b", r"\bscrum\s*master\b"
        ],
        "languages": ["SQL"],
        "frameworks": ["Jira", "Confluence", "Agile", "Scrum"],
        "specializations": ["Roadmapping", "Feature Prioritization", "Cross-Functional Leadership", "Technical Specs"]
    },

    # ── 13. IT SUPPORT & SYSTEMS ────────────────────────────────────
    "IT Support / Systems Administrator": {
        "family": "IT Support",
        "titles": [
            r"\bit\s*support\s*specialist\b", r"\bit\s*specialist\b", r"\bsystems\s*administrator\b",
            r"\bsysadmin\b", r"\bhelp\s*desk\s*technician\b", r"\bdesktop\s*support\b",
            r"\bit\s*administrator\b", r"\bit\s*operations\s*engineer\b"
        ],
        "languages": ["PowerShell", "Bash", "Python"],
        "frameworks": ["Active Directory", "Okta", "MDM (Jamf/Intune)", "ServiceNow"],
        "specializations": ["Hardware Provisioning", "User Access Management", "Troubleshooting", "Workstation OS"]
    }
}
