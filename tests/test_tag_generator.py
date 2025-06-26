"""Tests for the tag generation system."""

from unittest.mock import Mock, patch

import pytest

from airules.analyzer.data_models import (
    AnalysisResult,
    DeploymentInfo,
    DirectoryInfo,
    FrameworkCategory,
    FrameworkInfo,
    LanguageInfo,
    ProjectType,
    SecurityInfo,
    TestingInfo,
)
from airules.analyzer.tag_generator import TagGenerator
from airules.analyzer.tag_rules import (
    FRAMEWORK_TAG_MAPPING,
    MAX_TAGS_PER_PROJECT,
    MIN_TAGS_PER_PROJECT,
    PROJECT_TYPE_TAGS,
)
from airules.analyzer.tag_validator import TagValidator


class TestTagGenerator:
    """Test cases for TagGenerator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = TagGenerator()

    def create_sample_analysis_result(self) -> AnalysisResult:
        """Create a sample analysis result for testing."""
        return AnalysisResult(
            project_path="/test/project",
            project_type=ProjectType.WEB_FRONTEND,
            languages=LanguageInfo(
                primary_language="javascript",
                languages={"javascript": 0.8, "css": 0.2},
                file_extensions={".js", ".css", ".html"},
                total_files=50,
            ),
            frameworks=[
                FrameworkInfo(
                    name="react",
                    category=FrameworkCategory.FRONTEND,
                    version="18.2.0",
                    confidence=0.95,
                    package_name="react",
                    config_files=["package.json"],
                    indicators=["src/App.jsx", "public/index.html"],
                    tags=["components", "jsx"],
                ),
                FrameworkInfo(
                    name="webpack",
                    category=FrameworkCategory.BUNDLER,
                    confidence=0.85,
                    package_name="webpack",
                    config_files=["webpack.config.js"],
                ),
            ],
            directory_info=DirectoryInfo(
                has_src_dir=True,
                has_tests_dir=True,
                has_docs_dir=False,
                has_config_dir=True,
            ),
            testing_info=TestingInfo(
                has_unit_tests=True,
                test_frameworks=["jest"],
                test_directories=["src/__tests__"],
            ),
            security_info=SecurityInfo(),
            deployment_info=DeploymentInfo(),
        )

    def test_generate_tags_basic(self):
        """Test basic tag generation from analysis result."""
        analysis = self.create_sample_analysis_result()
        tags = self.generator.generate_tags(analysis)

        # Should have reasonable number of tags
        assert MIN_TAGS_PER_PROJECT <= len(tags) <= MAX_TAGS_PER_PROJECT

        # Should include framework tags
        assert "react" in tags
        assert "javascript" in tags

        # Should include project type tags
        assert "frontend" in tags or "web_frontend" in tags

        # Should include directory structure tags
        assert "testing" in tags  # has_tests_dir is True

    def test_framework_tag_generation(self):
        """Test framework-specific tag generation."""
        frameworks = [
            FrameworkInfo(
                name="django", category=FrameworkCategory.WEB_FRAMEWORK, confidence=0.9
            ),
            FrameworkInfo(
                name="postgresql", category=FrameworkCategory.DATABASE, confidence=0.8
            ),
        ]

        tags = self.generator._generate_framework_tags(frameworks)
        tag_names = [tag for tag, _ in tags]

        assert "django" in tag_names
        assert "postgresql" in tag_names
        assert "python" in tag_names  # Django implies Python
        assert "orm" in tag_names  # Django has ORM
        assert "database" in tag_names  # PostgreSQL category

    def test_language_tag_generation(self):
        """Test language-specific tag generation."""
        language_info = LanguageInfo(
            primary_language="python",
            languages={"python": 0.8, "javascript": 0.2},
            file_extensions={".py", ".js"},
            total_files=40,
        )

        tags = self.generator._generate_language_tags(language_info)
        tag_names = [tag for tag, _ in tags]

        assert "python" in tag_names
        assert "javascript" in tag_names
        assert "readable" in tag_names  # Python characteristic
        assert "dynamic" in tag_names  # Both languages are dynamic

    def test_project_type_tag_generation(self):
        """Test project type tag generation."""
        tags = self.generator._generate_project_type_tags(ProjectType.MICROSERVICE)
        tag_names = [tag for tag, _ in tags]

        assert "microservice" in tag_names
        assert "distributed" in tag_names
        assert "api" in tag_names
        assert "scalable" in tag_names

    def test_directory_tag_generation(self):
        """Test directory structure tag generation."""
        directory_info = DirectoryInfo(
            has_tests_dir=True,
            has_docs_dir=True,
            has_migrations_dir=True,
            monorepo_packages=["package1", "package2"],
        )

        tags = self.generator._generate_directory_tags(directory_info)
        tag_names = [tag for tag, _ in tags]

        assert "testing" in tag_names
        assert "documentation" in tag_names
        assert "database" in tag_names  # migrations suggest database
        assert "monorepo" in tag_names

    def test_testing_tag_generation(self):
        """Test testing-related tag generation."""
        testing_info = TestingInfo(
            has_unit_tests=True,
            has_integration_tests=True,
            has_e2e_tests=True,
            test_frameworks=["pytest", "selenium"],
            test_coverage_tools=["coverage.py"],
        )

        tags = self.generator._generate_testing_tags(testing_info)
        tag_names = [tag for tag, _ in tags]

        assert "unit-tests" in tag_names
        assert "integration-tests" in tag_names
        assert "e2e" in tag_names
        assert "testing" in tag_names
        assert "pytest" in tag_names
        assert "selenium" in tag_names
        assert "code-coverage" in tag_names

    def test_security_tag_generation(self):
        """Test security-related tag generation."""
        security_info = SecurityInfo(
            has_security_tools=True,
            has_env_files=True,
            has_secrets_config=True,
            authentication_methods=["oauth", "jwt"],
        )

        tags = self.generator._generate_security_tags(security_info)
        tag_names = [tag for tag, _ in tags]

        assert "security" in tag_names
        assert "environment-config" in tag_names
        assert "secrets-management" in tag_names
        assert "oauth" in tag_names
        assert "jwt" in tag_names

    def test_deployment_tag_generation(self):
        """Test deployment-related tag generation."""
        deployment_info = DeploymentInfo(
            containerized=True,
            container_tools=["docker", "kubernetes"],
            cloud_platforms=["aws", "azure"],
            ci_cd_tools=["github-actions", "jenkins"],
            infrastructure_as_code=["terraform"],
        )

        tags = self.generator._generate_deployment_tags(deployment_info)
        tag_names = [tag for tag, _ in tags]

        assert "containerization" in tag_names
        assert "docker" in tag_names
        assert "kubernetes" in tag_names
        assert "aws" in tag_names
        assert "ci-cd" in tag_names
        assert "infrastructure-as-code" in tag_names
        assert "devops" in tag_names

    def test_context_analysis(self):
        """Test contextual tag analysis."""
        analysis = self.create_sample_analysis_result()

        # Test API context
        analysis.frameworks.append(
            FrameworkInfo(
                name="express", category=FrameworkCategory.WEB_FRAMEWORK, confidence=0.9
            )
        )

        api_tags = self.generator._analyze_api_context(analysis)
        tag_names = [tag for tag, _ in api_tags]
        assert "rest-api" in tag_names

    def test_user_preferences_application(self):
        """Test application of user preferences."""
        tag_sources = {
            "frameworks": [("react", 0.8), ("vue", 0.7)],
            "languages": [("javascript", 0.9)],
        }

        preferences = {"preferred_tags": ["react"], "excluded_tags": ["vue"]}

        modified_sources = self.generator._apply_user_preferences(
            tag_sources, preferences
        )

        # React should be boosted
        react_scores = [
            score for tag, score in modified_sources["frameworks"] if tag == "react"
        ]
        assert react_scores[0] > 0.8  # Boosted from original 0.8

        # Vue should be excluded
        vue_tags = [tag for tag, _ in modified_sources["frameworks"] if tag == "vue"]
        assert len(vue_tags) == 0

    def test_tag_validation_integration(self):
        """Test integration with tag validation."""
        analysis = self.create_sample_analysis_result()
        tags = self.generator.generate_tags(analysis)

        # All tags should be valid
        for tag in tags:
            assert self.generator.validator.is_valid_tag(tag)

        # Should not have duplicates
        assert len(tags) == len(set(tags))

    def test_microservice_detection(self):
        """Test microservice-specific tag generation."""
        analysis = AnalysisResult(
            project_path="/microservice",
            project_type=ProjectType.MICROSERVICE,
            frameworks=[
                FrameworkInfo(
                    name="fastapi",
                    category=FrameworkCategory.WEB_FRAMEWORK,
                    confidence=0.9,
                )
            ],
            deployment_info=DeploymentInfo(containerized=True),
            languages=LanguageInfo(primary_language="python"),
        )

        tags = self.generator.generate_tags(analysis)

        assert "microservices" in tags
        assert "distributed" in tags
        assert "containerization" in tags
        assert "python" in tags
        assert "fastapi" in tags

    def test_monorepo_detection(self):
        """Test monorepo-specific tag generation."""
        analysis = AnalysisResult(
            project_path="/monorepo",
            directory_info=DirectoryInfo(
                monorepo_packages=["frontend", "backend", "shared"]
            ),
            languages=LanguageInfo(primary_language="typescript"),
        )

        tags = self.generator.generate_tags(analysis)

        assert "monorepo" in tags
        assert "multi-package" in tags
        assert "typescript" in tags

    def test_data_science_project_detection(self):
        """Test data science project tag generation."""
        analysis = AnalysisResult(
            project_path="/data-project",
            project_type=ProjectType.DATA_SCIENCE,
            frameworks=[
                FrameworkInfo(
                    name="pandas", category=FrameworkCategory.ANALYTICS, confidence=0.9
                ),
                FrameworkInfo(
                    name="numpy", category=FrameworkCategory.ANALYTICS, confidence=0.8
                ),
                FrameworkInfo(
                    name="scikit-learn",
                    category=FrameworkCategory.ANALYTICS,
                    confidence=0.8,
                ),
            ],
            languages=LanguageInfo(primary_language="python"),
        )

        tags = self.generator.generate_tags(analysis)

        assert "data-science" in tags
        assert "analytics" in tags
        assert "python" in tags

    def test_insufficient_tags_handling(self):
        """Test handling when insufficient tags are generated."""
        minimal_analysis = AnalysisResult(
            project_path="/minimal", languages=LanguageInfo(primary_language="python")
        )

        tags = self.generator.generate_tags(minimal_analysis)

        # Should still meet minimum requirements
        assert len(tags) >= MIN_TAGS_PER_PROJECT
        assert "python" in tags

    def test_tag_explanations(self):
        """Test tag explanation generation."""
        analysis = self.create_sample_analysis_result()
        tags = self.generator.generate_tags(analysis)
        explanations = self.generator.get_tag_explanations(tags, analysis)

        # Should have explanations for all tags
        assert len(explanations) == len(tags)

        # React should have framework explanation
        if "react" in tags:
            assert "framework" in explanations["react"].lower()

        # JavaScript should have language explanation
        if "javascript" in tags:
            assert "programming" in explanations["javascript"].lower()


class TestTagValidator:
    """Test cases for TagValidator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = TagValidator()

    def test_normalize_tag(self):
        """Test tag normalization."""
        assert self.validator.normalize_tag("React.js") == "react"
        assert self.validator.normalize_tag("  PYTHON  ") == "python"
        assert self.validator.normalize_tag("full stack") == "fullstack"
        assert self.validator.normalize_tag("unit-test") == "unit-tests"
        assert self.validator.normalize_tag("continuous integration") == "ci-cd"

    def test_is_valid_tag(self):
        """Test tag validation."""
        assert self.validator.is_valid_tag("react")
        assert self.validator.is_valid_tag("javascript")
        assert self.validator.is_valid_tag("full-stack")
        assert self.validator.is_valid_tag("web-development")

        # Invalid tags
        assert not self.validator.is_valid_tag("")
        assert not self.validator.is_valid_tag("1")  # Pure number
        assert not self.validator.is_valid_tag("@invalid")  # Invalid character
        assert not self.validator.is_valid_tag("a")  # Too short

    def test_remove_duplicates(self):
        """Test duplicate removal."""
        tags = ["react", "React", "REACT", "vue", "vue.js", "invalid@tag", ""]
        result = self.validator.remove_duplicates(tags)

        assert "react" in result
        assert "vue" in result
        assert result.count("react") == 1  # No duplicates
        assert "invalid@tag" not in result  # Invalid tag removed
        assert "" not in result  # Empty tag removed

    def test_apply_exclusion_rules(self):
        """Test exclusion rule application."""
        tags = ["mobile", "browser", "responsive", "api", "frontend"]
        result = self.validator.apply_exclusion_rules(tags)

        # Mobile projects shouldn't have browser-related tags
        assert "mobile" in result
        assert "browser" not in result
        assert "responsive" not in result

        # API projects shouldn't have frontend tags
        assert "api" in result
        assert "frontend" not in result

    def test_consolidate_groups(self):
        """Test tag group consolidation."""
        tags = ["html", "css", "javascript", "web", "other-tag"]
        result = self.validator.consolidate_groups(tags)

        # Should consolidate web development tags
        if (
            len([tag for tag in tags if tag in ["html", "css", "javascript", "web"]])
            >= 3
        ):
            assert "web-development" in result
            # Original tags should be removed
            for tag in ["html", "css", "javascript"]:
                assert tag not in result

    def test_prioritize_tags(self):
        """Test tag prioritization."""
        tags = ["react", "documentation", "assets", "testing", "performance"]
        result = self.validator.prioritize_tags(tags, max_tags=3)

        assert len(result) <= 3
        # Higher priority tags should be kept
        assert "react" in result  # High priority
        assert "testing" in result  # High priority

    def test_validate_tag_list(self):
        """Test complete tag list validation."""
        tags = ["React", "vue.js", "Testing", "invalid@", "", "react", "TESTING"]
        validated_tags, warnings = self.validator.validate_tag_list(tags)

        assert len(validated_tags) > 0
        assert len(warnings) > 0  # Should have warnings about duplicates/invalid

        # Check that duplicates were removed
        assert validated_tags.count("react") == 1
        assert validated_tags.count("testing") == 1

        # Invalid tags should be removed
        assert "invalid@" not in validated_tags
        assert "" not in validated_tags

    def test_suggest_missing_tags(self):
        """Test missing tag suggestions."""
        tags = ["testing", "database", "rest-api"]
        context = {"has_tests": True, "is_web_project": True}

        suggestions = self.validator.suggest_missing_tags(tags, context)

        # Should suggest complementary tags
        assert "unit-tests" in suggestions  # testing suggests unit-tests
        assert "json" in suggestions  # rest-api suggests json

    def test_calculate_tag_relevance_score(self):
        """Test tag relevance scoring."""
        context = {
            "frameworks": ["React", "Express"],
            "primary_language": "javascript",
            "project_type": ProjectType.FULLSTACK,
        }

        react_score = self.validator.calculate_tag_relevance_score("react", context)
        random_score = self.validator.calculate_tag_relevance_score(
            "random-tag", context
        )

        # React should have higher relevance in this context
        assert react_score > random_score
        assert 0.0 <= react_score <= 1.0
        assert 0.0 <= random_score <= 1.0

    def test_generate_tag_report(self):
        """Test tag validation report generation."""
        original_tags = ["React", "vue.js", "testing", "invalid@", "react"]
        final_tags = ["react", "vue", "testing"]
        warnings = ["Removed 1 duplicate/invalid tags"]

        report = self.validator.generate_tag_report(original_tags, final_tags, warnings)

        assert "Tag Validation Report" in report
        assert "Original tags: 5" in report
        assert "Final tags: 3" in report
        assert "Warnings:" in report
        assert "Removed 1 duplicate/invalid tags" in report
        assert "react" in report
        assert "vue" in report
        assert "testing" in report


class TestTagRulesIntegration:
    """Test integration with tag rules and mappings."""

    def test_framework_mapping_completeness(self):
        """Test that framework mappings are complete and valid."""
        for framework, tags in FRAMEWORK_TAG_MAPPING.items():
            assert isinstance(framework, str)
            assert len(framework) > 0
            assert isinstance(tags, list)
            assert len(tags) > 0

            for tag in tags:
                assert isinstance(tag, str)
                assert len(tag) > 0
                assert " " not in tag  # Tags should not contain spaces

    def test_project_type_mapping_completeness(self):
        """Test that project type mappings are complete."""
        for project_type, tags in PROJECT_TYPE_TAGS.items():
            assert isinstance(project_type, ProjectType)
            assert isinstance(tags, list)
            assert len(tags) > 0

            for tag in tags:
                assert isinstance(tag, str)
                assert len(tag) > 0

    def test_tag_generation_with_real_mappings(self):
        """Test tag generation using real framework mappings."""
        generator = TagGenerator()

        # Test React project
        react_framework = FrameworkInfo(
            name="react", category=FrameworkCategory.FRONTEND, confidence=0.9
        )

        tags = generator._generate_framework_tags([react_framework])
        tag_names = [tag for tag, _ in tags]

        # Should include React's mapped tags
        expected_react_tags = FRAMEWORK_TAG_MAPPING["react"]
        for expected_tag in expected_react_tags:
            assert expected_tag in tag_names

    def test_constants_sanity(self):
        """Test that constants are reasonable."""
        assert MIN_TAGS_PER_PROJECT >= 1
        assert MAX_TAGS_PER_PROJECT >= MIN_TAGS_PER_PROJECT
        assert MAX_TAGS_PER_PROJECT <= 20  # Reasonable upper bound
