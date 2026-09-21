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

    def test_systemd_unit_uses_deploy_checkout_and_venv(self):
        """The service unit should point at the deploy checkout and venv."""
        service = self._read(SERVICE_FILE)

        self.assertIn('WorkingDirectory=/srv/minecraft/chatsharepy', service)
        self.assertIn('EnvironmentFile=-/srv/minecraft/chatsharepy/.env', service)
        self.assertIn(
            'ExecStart=/srv/minecraft/chatsharepy/venv/bin/python -m src.chatshare',
            service,
        )

    def test_deploy_workflow_matches_service_paths(self):
        """The deploy workflow should use the same checkout and venv paths."""
        workflow = self._read(DEPLOY_WORKFLOW)
        service = self._read(SERVICE_FILE)

        app_dir_match = re.search(r'^\s+APP_DIR=(.+)$', workflow, re.MULTILINE)
        exec_start_match = re.search(r'^ExecStart=(.+)$', service, re.MULTILINE)
        env_file_match = re.search(r'^EnvironmentFile=-?(.+)$', service, re.MULTILINE)

        self.assertIsNotNone(app_dir_match)
        self.assertIsNotNone(exec_start_match)
        self.assertIsNotNone(env_file_match)

        app_dir = app_dir_match.group(1)

        self.assertEqual(
            f'{app_dir}/venv/bin/python -m src.chatshare',
            exec_start_match.group(1),
        )
        self.assertEqual(f'{app_dir}/.env', env_file_match.group(1))
        self.assertIn('VENV_PYTHON="$APP_DIR/venv/bin/python"', workflow)
        self.assertIn('cd "$APP_DIR"', workflow)
        self.assertIn('"$VENV_PYTHON" -m pip install -r requirements.txt', workflow)


if __name__ == '__main__':
    unittest.main()
