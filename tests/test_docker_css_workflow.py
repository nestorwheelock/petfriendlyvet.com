"""
Tests for T-081: Docker CSS Development Workflow

Validates that the docker-compose.override.yml is properly configured
to allow instant CSS changes during development without Docker rebuilds.
"""
import os
import pytest
import yaml
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


class TestDockerCSSWorkflow:
    """Test that Docker CSS development workflow is properly configured."""

    def test_docker_compose_override_exists(self):
        """docker-compose.override.yml should exist for dev workflow."""
        override_path = BASE_DIR / "docker-compose.override.yml"
        assert override_path.exists(), (
            "docker-compose.override.yml must exist for CSS dev workflow. "
            "This file enables instant CSS changes without Docker rebuilds."
        )

    def test_override_mounts_static_directory(self):
        """Override should mount local static directory for instant CSS changes."""
        override_path = BASE_DIR / "docker-compose.override.yml"
        if not override_path.exists():
            pytest.skip("docker-compose.override.yml not yet created")

        with open(override_path) as f:
            config = yaml.safe_load(f)

        # Check web service exists
        assert "services" in config, "Override must define services"
        assert "web" in config["services"], "Override must configure web service"

        web_service = config["services"]["web"]

        # Check volumes include static mount
        assert "volumes" in web_service, "Web service must define volumes"
        volumes = web_service["volumes"]

        # Look for static directory mount
        static_mounted = any(
            "./static" in str(v) or "static:" in str(v)
            for v in volumes
        )
        assert static_mounted, (
            "Web service must mount ./static directory for instant CSS changes. "
            "Expected volume like './static:/app/static:ro'"
        )

    def test_override_sets_debug_environment(self):
        """Override should set DJANGO_DEBUG=True for development."""
        override_path = BASE_DIR / "docker-compose.override.yml"
        if not override_path.exists():
            pytest.skip("docker-compose.override.yml not yet created")

        with open(override_path) as f:
            config = yaml.safe_load(f)

        web_service = config["services"]["web"]

        # Check environment includes debug setting
        assert "environment" in web_service, "Web service must define environment"
        env = web_service["environment"]

        # Environment can be list of KEY=VALUE or dict
        if isinstance(env, list):
            debug_set = any("DJANGO_DEBUG=True" in str(e) for e in env)
        else:
            debug_set = env.get("DJANGO_DEBUG") == "True" or env.get("DJANGO_DEBUG") is True

        assert debug_set, "Web service must set DJANGO_DEBUG=True for development"

    def test_main_compose_unchanged_for_production(self):
        """Main docker-compose.yml should remain unchanged for production use."""
        compose_path = BASE_DIR / "docker-compose.yml"
        assert compose_path.exists(), "docker-compose.yml must exist"

        with open(compose_path) as f:
            config = yaml.safe_load(f)

        # Verify it's a valid compose file
        assert "services" in config
        assert "web" in config["services"]

        # The main compose file should have the static_volume (for production)
        web_volumes = config["services"]["web"].get("volumes", [])
        has_static_volume = any("static_volume" in str(v) for v in web_volumes)
        assert has_static_volume, (
            "Main docker-compose.yml should retain static_volume for production. "
            "The override file handles dev-specific mounts."
        )


class TestDeploymentDocumentation:
    """Test that deployment documentation covers both workflows."""

    def test_deployment_docs_exist(self):
        """DEPLOYMENT.md should exist with workflow documentation."""
        docs_path = BASE_DIR / "docs" / "DEPLOYMENT.md"
        assert docs_path.exists(), (
            "docs/DEPLOYMENT.md must exist with deployment instructions"
        )

    def test_deployment_docs_cover_css_dev_workflow(self):
        """DEPLOYMENT.md should document CSS development workflow."""
        docs_path = BASE_DIR / "docs" / "DEPLOYMENT.md"
        if not docs_path.exists():
            pytest.skip("docs/DEPLOYMENT.md not yet created")

        content = docs_path.read_text()

        # Check for CSS development workflow section
        assert "css" in content.lower() or "static" in content.lower(), (
            "DEPLOYMENT.md must document CSS/static file development workflow"
        )

        # Check for npm commands
        assert "npm run dev" in content or "npm run build" in content, (
            "DEPLOYMENT.md must document npm commands for CSS compilation"
        )

    def test_deployment_docs_cover_production_workflow(self):
        """DEPLOYMENT.md should document production deployment workflow."""
        docs_path = BASE_DIR / "docs" / "DEPLOYMENT.md"
        if not docs_path.exists():
            pytest.skip("docs/DEPLOYMENT.md not yet created")

        content = docs_path.read_text()

        # Check for production deployment instructions
        has_prod_instructions = (
            "docker-compose.yml" in content or
            "production" in content.lower() or
            "-f docker-compose.yml" in content
        )
        assert has_prod_instructions, (
            "DEPLOYMENT.md must document production deployment workflow"
        )

    def test_deployment_docs_explain_override_behavior(self):
        """DEPLOYMENT.md should explain that override is auto-loaded in dev."""
        docs_path = BASE_DIR / "docs" / "DEPLOYMENT.md"
        if not docs_path.exists():
            pytest.skip("docs/DEPLOYMENT.md not yet created")

        content = docs_path.read_text()

        # Check for explanation of override behavior
        has_override_explanation = (
            "override" in content.lower() or
            "auto-load" in content.lower() or
            "-f docker-compose.yml" in content  # How to avoid override
        )
        assert has_override_explanation, (
            "DEPLOYMENT.md must explain docker-compose.override.yml behavior "
            "and how to bypass it for production"
        )
