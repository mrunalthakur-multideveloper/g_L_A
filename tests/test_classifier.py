"""
Comprehensive Unit Tests for IT Job Classification Engine
Verifies IT/Non-IT gate, domain scoring, technology extraction, and seniority detection.
"""

import unittest
from models.job import NormalizedJob
from classification.classifier import classify_job
from classification.non_it import evaluate_non_it_purpose
from classification.technology_extractor import extract_technologies, extract_specializations
from classification.seniority import detect_seniority


class TestJobClassifier(unittest.TestCase):

    def test_it_vs_non_it_gate(self):
        # 1. Pure IT Roles
        job_swe = NormalizedJob(title="Senior Software Engineer", description="Build web apps in Python and React.")
        self.assertTrue(classify_job(job_swe).is_it_job)
        
        job_ml = NormalizedJob(title="Machine Learning Engineer", description="Train models with PyTorch and AWS.")
        self.assertTrue(classify_job(job_ml).is_it_job)
        
        # 2. Non-IT Roles with incidental tech mentions
        job_fin = NormalizedJob(
            title="Financial Analyst",
            description="Perform financial analysis, budgeting, and modeling using Python, SQL, AWS, Tableau, and Excel."
        )
        self.assertFalse(classify_job(job_fin).is_it_job)
        
        job_mech = NormalizedJob(
            title="Mechanical Engineer",
            description="Design hardware components using SolidWorks, CAD, Python, and MATLAB."
        )
        self.assertFalse(classify_job(job_mech).is_it_job)
        
        job_hr = NormalizedJob(
            title="HR Specialist",
            description="Manage onboarding and talent acquisition data using SQL and Workday."
        )
        self.assertFalse(classify_job(job_hr).is_it_job)
        
        job_nurse = NormalizedJob(
            title="Registered Nurse (RN) - ICU",
            description="Patient care in intensive care unit."
        )
        self.assertFalse(classify_job(job_nurse).is_it_job)
        
        job_driver = NormalizedJob(
            title="Delivery Driver (CDL-A)",
            description="Transport logistics and freight."
        )
        self.assertFalse(classify_job(job_driver).is_it_job)

    def test_domain_classification_precision(self):
        # Java Backend
        job_java = NormalizedJob(
            title="Java Backend Engineer",
            description="Develop microservices using Java, Spring Boot, Hibernate, REST API, PostgreSQL, and AWS."
        )
        classified_java = classify_job(job_java)
        self.assertTrue(classified_java.is_it_job)
        self.assertEqual(classified_java.it_job_family, "Software Engineering")
        self.assertEqual(classified_java.job_domain, "Java Developer")
        self.assertIn("Backend Developer", classified_java.job_domains)

        # Angular Developer
        job_angular = NormalizedJob(
            title="Angular Developer",
            description="Build single page applications using Angular, TypeScript, RxJS, HTML, CSS."
        )
        classified_angular = classify_job(job_angular)
        self.assertEqual(classified_angular.job_domain, "Angular Developer")
        self.assertIn("Frontend Developer", classified_angular.job_domains)

        # Machine Learning Engineer (Must NOT be Python Developer)
        job_mle = NormalizedJob(
            title="Machine Learning Engineer",
            description="Train LLM models using Python, PyTorch, TensorFlow, Transformers, and RAG on AWS."
        )
        classified_mle = classify_job(job_mle)
        self.assertEqual(classified_mle.job_domain, "Machine Learning Engineer")
        self.assertNotEqual(classified_mle.job_domain, "Python Developer")
        self.assertEqual(classified_mle.it_job_family, "AI / Machine Learning")

        # DevOps Engineer (Must NOT be Python Developer)
        job_devops = NormalizedJob(
            title="Senior DevOps Engineer",
            description="Automate CI/CD pipelines using AWS, Docker, Kubernetes, Terraform, Jenkins, and Prometheus."
        )
        classified_devops = classify_job(job_devops)
        self.assertEqual(classified_devops.job_domain, "DevOps Engineer")
        self.assertEqual(classified_devops.job_level, "Senior")
        self.assertIn("Cloud Engineer", classified_devops.job_domains)

        # Data Engineer (Must NOT be Python Developer)
        job_de = NormalizedJob(
            title="Data Engineer",
            description="Build ETL pipelines using Python, SQL, Spark, Kafka, Airflow, and Snowflake on AWS."
        )
        classified_de = classify_job(job_de)
        self.assertEqual(classified_de.job_domain, "Data Engineer")
        self.assertNotEqual(classified_de.job_domain, "Python Developer")
        self.assertEqual(classified_de.it_job_family, "Data")

    def test_multi_domain_and_technology_extraction(self):
        job_fullstack = NormalizedJob(
            title="Senior Full Stack Engineer",
            description="Build end-to-end applications using Java, Spring Boot, Angular, TypeScript, PostgreSQL, AWS, Docker, and Kubernetes."
        )
        classified = classify_job(job_fullstack)
        self.assertEqual(classified.job_domain, "Full Stack Developer")
        self.assertIn("Java Developer", classified.job_domains)
        self.assertIn("Angular Developer", classified.job_domains)
        
        # Verify categorized tech extraction
        techs = classified.technologies
        self.assertIn("Java", techs["programming_languages"])
        self.assertIn("TypeScript", techs["programming_languages"])
        self.assertIn("Spring Boot", techs["frameworks"])
        self.assertIn("Angular", techs["frameworks"])
        self.assertIn("PostgreSQL", techs["databases"])
        self.assertIn("AWS", techs["cloud"])
        self.assertIn("Docker", techs["containers_iac"])
        self.assertIn("Kubernetes", techs["containers_iac"])

    def test_experience_extraction(self):
        from classification.experience import extract_experience
        
        # 1. Numerical years with plus
        self.assertEqual(extract_experience("Requires 5+ years of software engineering experience in Python."), "5+ years")
        
        # 2. Numerical range
        self.assertEqual(extract_experience("Minimum 3-5 years of hands-on experience with AWS."), "3-5 years")
        
        # 3. Leading / managing role
        self.assertEqual(extract_experience("8+ years leading security engineering teams."), "8+ years")
        
        # 4. Entry level / internship
        self.assertEqual(extract_experience("Summer Software Engineering Internship 2026."), "0-1 years (Internship)")
        self.assertEqual(extract_experience("New grad software engineer position."), "0-1 years (Entry Level)")
        
        # 5. Fallback from seniority level
        self.assertEqual(extract_experience("Software development role.", level="Senior"), "5+ years (Senior)")


if __name__ == "__main__":
    unittest.main()
