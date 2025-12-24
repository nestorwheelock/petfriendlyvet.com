"""Services for bug creation and error tracking."""
import logging
from pathlib import Path
from typing import Optional, Tuple

from django.conf import settings
from django.utils.text import slugify

from .models import KnownBug

logger = logging.getLogger(__name__)


class BugCreationService:
    """Service for creating bug reports and GitHub issues."""

    def get_next_bug_id(self) -> str:
        """Get the next sequential bug ID (B-XXX format)."""
        last_bug = KnownBug.all_objects.order_by('-bug_id').first()
        if last_bug:
            try:
                num = int(last_bug.bug_id.split('-')[1]) + 1
            except (ValueError, IndexError):
                num = 1
        else:
            num = 1
        return f"B-{num:03d}"

    def format_bug_content(self, bug_id: str, data: dict) -> str:
        """Format bug report as markdown content."""
        return f"""# {bug_id}: {data['title']}

**Severity**: {data.get('severity', 'unknown').capitalize()}
**Status**: Open
**Error Type**: {data.get('error_type', 'unknown')}
**Status Code**: {data.get('status_code', 'N/A')}

## Description

{data.get('description', 'No description provided.')}

## Steps to Reproduce

1. Navigate to URL pattern: `{data.get('url_pattern', 'N/A')}`
2. The error occurs automatically

## Technical Details

- **Fingerprint**: `{data.get('fingerprint', 'N/A')}`
- **Error Type**: {data.get('error_type', 'unknown')}
- **HTTP Status**: {data.get('status_code', 'N/A')}

## Definition of Done

- [ ] Root cause identified
- [ ] Fix implemented
- [ ] Tests written to prevent regression
- [ ] Fix verified in production
"""

    def create_bug_file(
        self,
        bug_id: str,
        data: dict,
        base_dir: Optional[Path] = None
    ) -> Path:
        """Create a bug report markdown file.

        Args:
            bug_id: The bug ID (e.g., B-001)
            data: Bug data including title, description, severity, etc.
            base_dir: Base directory for planning/tasks (defaults to settings.BASE_DIR)

        Returns:
            Path to the created file
        """
        if base_dir is None:
            base_dir = Path(settings.BASE_DIR)

        # Create planning/tasks directory if it doesn't exist
        tasks_dir = base_dir / 'planning' / 'tasks'
        tasks_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        title_slug = slugify(data.get('title', 'unknown-error'))[:50]
        filename = f"{bug_id}-{title_slug}.md"
        filepath = tasks_dir / filename

        # Write content
        content = self.format_bug_content(bug_id, data)
        filepath.write_text(content)

        logger.info("Created bug file: %s", filepath)
        return filepath

    def create_github_issue(
        self,
        bug_id: str,
        data: dict
    ) -> Tuple[Optional[int], str]:
        """Create a GitHub issue using GitHub REST API.

        Args:
            bug_id: The bug ID (e.g., B-001)
            data: Bug data including title, description, severity

        Returns:
            Tuple of (issue_number, issue_url) or (None, '') on failure
        """
        import httpx

        # Get GitHub configuration from settings
        github_token = getattr(settings, 'GITHUB_TOKEN', None)
        github_repo = getattr(settings, 'GITHUB_REPO', None)

        if not github_token or not github_repo:
            logger.warning(
                "GitHub token or repo not configured. "
                "Set GITHUB_TOKEN and GITHUB_REPO in settings."
            )
            return None, ''

        title = f"{bug_id}: {data.get('title', 'Unknown Error')}"
        body = f"""## Description

{data.get('description', 'Auto-generated bug report from error tracking.')}

## Severity

**{data.get('severity', 'unknown').capitalize()}**

## Technical Details

- Bug ID: {bug_id}
- Error Type: {data.get('error_type', 'unknown')}
- Status Code: {data.get('status_code', 'N/A')}
- URL Pattern: {data.get('url_pattern', 'N/A')}

---
*This issue was automatically created by the error tracking system.*
"""

        # Map severity to labels
        labels = ['bug']
        severity = data.get('severity', 'medium')
        if severity in ['critical', 'high', 'medium', 'low']:
            labels.append(severity)

        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(
                    f"https://api.github.com/repos/{github_repo}/issues",
                    headers={
                        "Authorization": f"Bearer {github_token}",
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28",
                    },
                    json={
                        "title": title,
                        "body": body,
                        "labels": labels,
                    },
                )

                if response.status_code != 201:
                    logger.error(
                        "Failed to create GitHub issue: %s %s",
                        response.status_code, response.text
                    )
                    return None, ''

                issue_data = response.json()
                issue_number = issue_data.get('number')
                issue_url = issue_data.get('html_url', '')

                logger.info("Created GitHub issue #%s: %s", issue_number, issue_url)
                return issue_number, issue_url

        except httpx.TimeoutException:
            logger.error("GitHub API request timed out")
            return None, ''
        except Exception as e:
            logger.exception("Failed to create GitHub issue: %s", e)
            return None, ''

    def create_full_bug(
        self,
        error_data: dict,
        base_dir: Optional[Path] = None
    ) -> KnownBug:
        """Create a complete bug report with file and GitHub issue.

        Args:
            error_data: Error data from error tracking
            base_dir: Base directory for planning/tasks

        Returns:
            Created KnownBug instance
        """
        bug_id = self.get_next_bug_id()

        # Try to create bug file (may fail in containerized production)
        try:
            self.create_bug_file(bug_id, error_data, base_dir)
        except (PermissionError, OSError) as e:
            logger.warning(
                "Could not create bug file for %s (container filesystem?): %s",
                bug_id, e
            )

        # Create GitHub issue
        issue_number, issue_url = self.create_github_issue(bug_id, error_data)

        # Create database record
        bug = KnownBug.objects.create(
            bug_id=bug_id,
            fingerprint=error_data.get('fingerprint', ''),
            github_issue_number=issue_number,
            github_issue_url=issue_url,
            title=error_data.get('title', 'Unknown Error'),
            description=error_data.get('description', ''),
            severity=error_data.get('severity', 'medium'),
            status='open',
            occurrence_count=1,
        )

        logger.info(
            "Created full bug report: %s (GitHub #%s)",
            bug_id, issue_number
        )
        return bug
