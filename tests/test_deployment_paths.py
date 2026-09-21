#!/usr/bin/env python3

"""
Regression tests for deployment path alignment.
"""

import re
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
SERVICE_FILE = REPOSITORY_ROOT / 'chatshare.service'
DEPLOY_WORKFLOW = REPOSITORY_ROOT / '.github' / 'workflows' / 'deploy.yml'


class TestDeploymentPaths(unittest.TestCase):
    """
    Ensure the deployment workflow and systemd unit stay aligned.
    """

    @staticmethod
    def _read(path):
        return path.read_text(encoding='utf-8')

    def test_systemd_unit_uses_production_paths(self):
        """The service unit should keep the production checkout and interpreter."""
        service = self._read(SERVICE_FILE)

        self.assertIn('WorkingDirectory=/srv/minecraft/chatsharepy', service)
        self.assertIn('EnvironmentFile=-/srv/minecraft/chatsharepy/.env', service)
        self.assertIn(
            'ExecStart=/usr/bin/python3 -m src.chatshare',
            service,
        )

    def test_deploy_workflow_matches_service_paths(self):
        """The deploy workflow should use the same checkout and interpreter paths."""
        workflow = self._read(DEPLOY_WORKFLOW)
        service = self._read(SERVICE_FILE)

        app_dir_match = re.search(r'^\s+APP_DIR=(.+)$', workflow, re.MULTILINE)
        exec_start_match = re.search(r'^ExecStart=(.+)$', service, re.MULTILINE)
        env_file_match = re.search(r'^EnvironmentFile=-?(.+)$', service, re.MULTILINE)
        python_bin_match = re.search(r'^\s+PYTHON_BIN=(.+)$', workflow, re.MULTILINE)

        self.assertIsNotNone(app_dir_match)
        self.assertIsNotNone(exec_start_match)
        self.assertIsNotNone(env_file_match)
        self.assertIsNotNone(python_bin_match)

        app_dir = app_dir_match.group(1)

        self.assertEqual(f'{python_bin_match.group(1)} -m src.chatshare', exec_start_match.group(1))
        self.assertEqual(f'{app_dir}/.env', env_file_match.group(1))
        self.assertIn('cd "$APP_DIR"', workflow)
        self.assertIn('"$PYTHON_BIN" -m pip install -r requirements.txt', workflow)


if __name__ == '__main__':
    unittest.main()
