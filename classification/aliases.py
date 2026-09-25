"""
Canonical Aliases and Text Normalization Module
Handles spelling variations, casing, punctuation, abbreviations, and technology aliases.
"""

import re

# Canonical mapping for programming languages and tools
CANONICAL_ALIASES = {
    # Languages
    "golang": "Go",
    "go lang": "Go",
    "cpp": "C++",
    "c plus plus": "C++",
    "c#": "C#",
    "c sharp": "C#",
    ".net": ".NET",
    "dotnet": ".NET",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "py": "Python",
    "python": "Python",
    "ruby on rails": "Ruby on Rails",
    "rails": "Ruby on Rails",
    "node": "Node.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    
    # Frameworks & Libraries
    "react": "React",
    "react.js": "React",
    "reactjs": "React",
    "react native": "React Native",
    "react-native": "React Native",
    "angular": "Angular",
    "angular.js": "AngularJS",
    "angularjs": "AngularJS",
    "vue": "Vue",
    "vue.js": "Vue",
    "vuejs": "Vue",
    "spring": "Spring",
    "spring boot": "Spring Boot",
    "springboot": "Spring Boot",
    "fastapi": "FastAPI",
    "fast api": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "express": "Express",
    "express.js": "Express",
    "expressjs": "Express",
    "nest": "NestJS",
    "nestjs": "NestJS",
    "next": "Next.js",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "nuxt": "Nuxt",
    "nuxt.js": "Nuxt",
    
    # AI / ML
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",
    "ai": "Artificial Intelligence",
    "artificial intelligence": "Artificial Intelligence",
    "dl": "Deep Learning",
    "deep learning": "Deep Learning",
    "nlp": "Natural Language Processing",
    "natural language processing": "Natural Language Processing",
    "llm": "Large Language Models",
    "llms": "Large Language Models",
    "large language models": "Large Language Models",
    "genai": "Generative AI",
    "gen ai": "Generative AI",
    "generative ai": "Generative AI",
    "cv": "Computer Vision",
    "computer vision": "Computer Vision",
    "rag": "RAG",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "tf": "TensorFlow",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    
    # Cloud & DevOps
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "tf": "Terraform",
    "terraform": "Terraform",
    "gcp": "Google Cloud",
    "google cloud platform": "Google Cloud",
    "google cloud": "Google Cloud",
    "aws": "AWS",
    "amazon web services": "AWS",
    "azure": "Azure",
    "microsoft azure": "Azure",
    "sre": "Site Reliability Engineering",
    "site reliability engineering": "Site Reliability Engineering",
    "devops": "DevOps",
    "devsecops": "DevSecOps",
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    
    # Databases
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "ms sql": "SQL Server",
    "mssql": "SQL Server",
    "sql server": "SQL Server",
    
    # QA
    "sdet": "SDET",
    "qa": "QA",
    "quality assurance": "Quality Assurance",
}


def normalize_token(text: str) -> str:
    """Normalize a word or title token for robust regex matching"""
    if not text:
        return ""
    # Lowercase, replace non-alphanumeric with spaces, collapse spaces
    cleaned = re.sub(r'[^a-zA-Z0-9\+\#\.]+', ' ', text.lower()).strip()
    return re.sub(r'\s+', ' ', cleaned)
