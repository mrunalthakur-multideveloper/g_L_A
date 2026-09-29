import unittest
from models.job import NormalizedJob
from classification.enrichment import enrich_job, parse_experience_range, extract_salary_info, extract_emails_from_text
from database.postgres import format_job_for_links_table, to_tuple_record


class TestJobEnrichmentAndDatabase(unittest.TestCase):

    def test_enrich_job_us(self):
        desc = """
        We are seeking a Lead Backend Developer to join our team in San Francisco, CA.
        Required Qualifications:
        - 5+ years of software engineering experience with Python and PostgreSQL.
        - Experience with AWS and Docker.
        - Inquiries: contact@innovatecorp.com
        Salary range: $150,000 - $190,000 per year.
        Visa sponsorship is not available for this position.
        """
        job = NormalizedJob(
            id="test-us-101",
            job_id="test-us-101",
            source="greenhouse",
            title="Lead Backend Developer",
            company_name="Innovate Corp",
            description=desc,
            location_display="San Francisco, CA"
        )
        enrich_job(job)

        self.assertEqual(job.job_level, "Lead")
        self.assertIn("5+ years", job.experience)
        self.assertEqual(job.experience_min, 5)
        self.assertIsNone(job.experience_max)
        self.assertEqual(job.job_type, "Full-time")
        self.assertEqual(job.location_city, "San Francisco")
        self.assertEqual(job.location_state, "CA")
        self.assertEqual(job.location_country, "USA")
        self.assertFalse(job.is_remote)
        self.assertIn("contact@innovatecorp.com", job.emails)
        self.assertEqual(job.compensation_min, 150000.0)
        self.assertEqual(job.compensation_max, 190000.0)
        self.assertEqual(job.compensation_currency, "USD")
        self.assertEqual(job.compensation_interval, "yearly")
        self.assertIn("$150,000 - $190,000", job.salary_text)

    def test_enrich_job_ireland(self):
        desc = """
        Frontend Engineer role based in Dublin, Ireland. Remote optional.
        Requirements:
        - 3-5 years experience in React, TypeScript, and CSS.
        - Email resumes to recruitment@irelandtech.ie
        Salary: €60,000 - €80,000 per year.
        """
        job = NormalizedJob(
            id="test-ie-202",
            job_id="test-ie-202",
            source="lever",
            title="Frontend Engineer",
            company_name="Ireland Tech",
            description=desc,
            location_display="Dublin, Ireland"
        )
        enrich_job(job)

        self.assertEqual(job.job_level, "Mid-Level")
        self.assertEqual(job.experience_min, 3)
        self.assertEqual(job.experience_max, 5)
        self.assertEqual(job.location_city, "Dublin")
        self.assertEqual(job.location_country, "Ireland")
        self.assertTrue(job.is_remote)
        self.assertIn("recruitment@irelandtech.ie", job.emails)
        self.assertEqual(job.compensation_min, 60000.0)
        self.assertEqual(job.compensation_max, 80000.0)
        self.assertEqual(job.compensation_currency, "EUR")

    def test_database_format_all_34_columns(self):
        desc = "Seeking Python Engineer with 2-4 years experience. Email hr@pycorp.com. $100k - $130k"
        job = NormalizedJob(
            id="gh:999888",
            job_id="gh:999888",
            source="greenhouse",
            title="Python Engineer",
            company_name="Py Corp",
            description=desc,
            location_display="New York, NY"
        )
        formatted = format_job_for_links_table(job)

        # Ensure all 34 database columns are present in formatted record
        expected_columns = [
            "job_id", "title", "company_name", "company_url", "company_logo",
            "location_city", "location_state", "location_country", "location_display",
            "description", "date_posted", "scraped_at", "job_url", "apply_url",
            "job_type", "job_level", "company_industry", "job_function",
            "is_remote", "is_easy_apply", "compensation_min", "compensation_max",
            "compensation_currency", "compensation_interval", "emails",
            "search_keyword", "experience", "salary_text", "created_at",
            "skills", "sponsorship_h1b", "source", "experience_min", "experience_max"
        ]
        self.assertEqual(len(expected_columns), 34)
        for col in expected_columns:
            self.assertIn(col, formatted, f"Missing column {col} in formatted record")

        self.assertEqual(formatted["job_id"], "999888")
        self.assertEqual(formatted["location_city"], "New York")
        self.assertEqual(formatted["location_state"], "NY")
        self.assertEqual(formatted["location_country"], "USA")
        self.assertEqual(formatted["job_level"], "Mid-Level")
        self.assertEqual(formatted["job_type"], "Full-time")
        self.assertEqual(formatted["experience_min"], 2)
        self.assertEqual(formatted["experience_max"], 4)
        self.assertIsNotNone(formatted["company_url"])

        # Test tuple conversion
        tpl = to_tuple_record(formatted)
        self.assertEqual(len(tpl), 34)


if __name__ == "__main__":
    unittest.main()
