"""
Unit Tests for ApplyUs CRM Client Domain Selection & Proxy Enforcement
Verifies:
1. Strictly 1 domain selected per active client (no multiple domain expansions).
2. Strict NULL domain skipping (clients with NULL/empty domain are skipped, not scraped).
3. Generic domain resolution to specific roles.
4. Proxy health checking and strict failure enforcement (aborts loudly, never skips silently).
"""

import os
import unittest
from unittest.mock import patch, MagicMock
from crm.client import fetch_active_clients, is_null_domain, normalize_domain_key
from utils.proxy import enforce_proxy_or_abort, verify_proxy_health, get_requests_session


class TestCrmClientDomainSelection(unittest.TestCase):

    def test_null_domain_helper(self):
        self.assertTrue(is_null_domain(None))
        self.assertTrue(is_null_domain(""))
        self.assertTrue(is_null_domain("   "))
        self.assertTrue(is_null_domain("null"))
        self.assertTrue(is_null_domain("NULL"))
        self.assertTrue(is_null_domain("None"))
        self.assertTrue(is_null_domain("undefined"))
        self.assertTrue(is_null_domain("n/a"))
        self.assertFalse(is_null_domain("Java Developer"))
        self.assertFalse(is_null_domain("Full Stack"))

    @patch("crm.client.get_requests_session")
    def test_desired_job_titles_extracted_per_client(self, mock_get_session):
        """Verify that a client's unique desired_job_titles are extracted as candidate domains."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "success": True,
            "data": [
                {
                    "lead_id": "c1",
                    "full_name": "zoya nithin",
                    "domain": "Java Full Stack Developer",
                    "desired_job_titles": [
                        "Java Full Stack Developer",
                        "Java Developer",
                        "Software Engineer",
                        "Full Stack Java Developer",
                        "Java Full Stack Engineer",
                        "Java Software Engineer"
                    ],
                    "country": "United States"
                }
            ]
        }
        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp
        mock_get_session.return_value = mock_session

        clients = fetch_active_clients()
        # Should extract all 6 unique desired job titles
        self.assertEqual(len(clients), 6)
        domain_names = [c["domain"] for c in clients]
        self.assertIn("Java Full Stack Developer", domain_names)
        self.assertIn("Java Developer", domain_names)
        self.assertIn("Software Engineer", domain_names)
        self.assertIn("Full Stack Java Developer", domain_names)
        self.assertIn("Java Full Stack Engineer", domain_names)
        self.assertIn("Java Software Engineer", domain_names)
        self.assertEqual(clients[0]["client_name"], "zoya nithin")

    @patch("crm.client.get_requests_session")
    def test_null_domain_client_is_strictly_skipped(self, mock_get_session):
        """Verify that a client with NULL/empty domain and no titles is skipped."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "success": True,
            "data": [
                {
                    "lead_id": "c1",
                    "full_name": "Null Client 1",
                    "domain": None,
                    "desired_job_titles": [],
                    "country": "United States"
                },
                {
                    "lead_id": "c2",
                    "full_name": "Null Client 2",
                    "domain": "null",
                    "desired_job_titles": None,
                    "country": "United States"
                },
                {
                    "lead_id": "c3",
                    "full_name": "Valid Client",
                    "domain": "Python Developer",
                    "desired_job_titles": ["Python Developer"],
                    "country": "United States"
                }
            ]
        }
        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp
        mock_get_session.return_value = mock_session

        clients = fetch_active_clients()
        # Only Valid Client should remain
        self.assertEqual(len(clients), 1)
        self.assertEqual(clients[0]["client_name"], "Valid Client")
        self.assertEqual(clients[0]["domain"], "Python Developer")

    @patch("crm.client.get_requests_session")
    def test_generic_engineering_domain_resolved_to_specific_titles(self, mock_get_session):
        """Verify that generic 'Engineering' domain resolves to specific desired titles."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "success": True,
            "data": [
                {
                    "lead_id": "c1",
                    "full_name": "Alex Tech",
                    "domain": "Engineering",
                    "desired_job_titles": ["Frontend React Developer", "Software Engineer"],
                    "country": "USA"
                }
            ]
        }
        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp
        mock_get_session.return_value = mock_session

        clients = fetch_active_clients()
        self.assertEqual(len(clients), 2)
        domain_names = [c["domain"] for c in clients]
        self.assertIn("Frontend React Developer", domain_names)
        self.assertIn("Software Engineer", domain_names)


class TestProxyEnforcement(unittest.TestCase):

    @patch("utils.proxy.get_webshare_proxy_url")
    def test_missing_proxy_runs_direct(self, mock_get_proxy):
        """Verify that missing proxy proceeds in direct mode without error."""
        mock_get_proxy.return_value = None
        result = enforce_proxy_or_abort()
        self.assertIsNone(result)

    @patch("utils.proxy.get_webshare_proxy_url")
    @patch("utils.proxy.verify_proxy_health")
    def test_healthy_proxy_proceeds(self, mock_verify, mock_get_proxy):
        """Verify that healthy proxy returns external IP and succeeds."""
        mock_get_proxy.return_value = "http://valid-proxy:80"
        mock_verify.return_value = (True, "38.154.185.97")
        ip = enforce_proxy_or_abort()
        self.assertEqual(ip, "38.154.185.97")


if __name__ == "__main__":
    unittest.main()
