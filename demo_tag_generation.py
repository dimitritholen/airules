#!/usr/bin/env python3
"""
Demonstration of the intelligent tag generation system.

This script shows how the tag generation works for different types of projects.
"""

from airules.analyzer.tag_generator import TagGenerator
from airules.analyzer.data_models import (
    AnalysisResult,
    FrameworkInfo,
    LanguageInfo,
    DirectoryInfo,
    TestingInfo,
    SecurityInfo,
    DeploymentInfo,
    ProjectType,
    FrameworkCategory,
)


def create_react_frontend_project():
    """Create a sample React frontend project analysis."""
    return AnalysisResult(
        project_path="/projects/react-app",
        project_type=ProjectType.WEB_FRONTEND,
        languages=LanguageInfo(
            primary_language="javascript",
            languages={"javascript": 0.7, "typescript": 0.2, "css": 0.1},
            file_extensions={".js", ".ts", ".jsx", ".tsx", ".css", ".scss"},
            total_files=120
        ),
        frameworks=[
            FrameworkInfo(
                name="react",
                category=FrameworkCategory.FRONTEND,
                version="18.2.0",
                confidence=0.95,
                package_name="react",
                config_files=["package.json"],
                indicators=["src/App.jsx", "src/components/"],
                tags=["components", "jsx"]
            ),
            FrameworkInfo(
                name="webpack",
                category=FrameworkCategory.BUNDLER,
                confidence=0.85,
                config_files=["webpack.config.js"]
            ),
            FrameworkInfo(
                name="jest",
                category=FrameworkCategory.TESTING,
                confidence=0.8,
                config_files=["jest.config.js"]
            )
        ],
        directory_info=DirectoryInfo(
            has_src_dir=True,
            has_tests_dir=True,
            has_docs_dir=False,
            has_config_dir=True,
            has_assets_dir=True,
            has_static_dir=True
        ),
        testing_info=TestingInfo(
            has_unit_tests=True,
            test_frameworks=["jest", "react-testing-library"],
            test_directories=["src/__tests__", "src/components/__tests__"]
        ),
        security_info=SecurityInfo(),
        deployment_info=DeploymentInfo(
            ci_cd_tools=["github-actions"]
        )
    )


def create_django_backend_project():
    """Create a sample Django backend project analysis."""
    return AnalysisResult(
        project_path="/projects/django-api",
        project_type=ProjectType.WEB_BACKEND,
        languages=LanguageInfo(
            primary_language="python",
            languages={"python": 0.9, "sql": 0.1},
            file_extensions={".py", ".sql"},
            total_files=80
        ),
        frameworks=[
            FrameworkInfo(
                name="django",
                category=FrameworkCategory.WEB_FRAMEWORK,
                version="4.2.0",
                confidence=0.95,
                config_files=["manage.py", "settings.py"]
            ),
            FrameworkInfo(
                name="postgresql",
                category=FrameworkCategory.DATABASE,
                confidence=0.9,
                config_files=["requirements.txt"]
            ),
            FrameworkInfo(
                name="pytest",
                category=FrameworkCategory.TESTING,
                confidence=0.8
            )
        ],
        directory_info=DirectoryInfo(
            has_src_dir=False,
            has_tests_dir=True,
            has_docs_dir=True,
            has_migrations_dir=True,
            has_config_dir=True
        ),
        testing_info=TestingInfo(
            has_unit_tests=True,
            has_integration_tests=True,
            test_frameworks=["pytest", "django-test"],
            test_coverage_tools=["coverage.py"]
        ),
        security_info=SecurityInfo(
            has_security_tools=True,
            has_env_files=True,
            authentication_methods=["jwt", "oauth"]
        ),
        deployment_info=DeploymentInfo(
            containerized=True,
            container_tools=["docker"],
            cloud_platforms=["aws"],
            ci_cd_tools=["github-actions"],
            infrastructure_as_code=["terraform"]
        )
    )


def create_microservice_project():
    """Create a sample microservice project analysis."""
    return AnalysisResult(
        project_path="/projects/user-service",
        project_type=ProjectType.MICROSERVICE,
        languages=LanguageInfo(
            primary_language="go",
            languages={"go": 0.95, "yaml": 0.05},
            file_extensions={".go", ".yaml", ".yml"},
            total_files=45
        ),
        frameworks=[
            FrameworkInfo(
                name="gin",
                category=FrameworkCategory.WEB_FRAMEWORK,
                confidence=0.9
            ),
            FrameworkInfo(
                name="postgresql",
                category=FrameworkCategory.DATABASE,
                confidence=0.8
            )
        ],
        directory_info=DirectoryInfo(
            has_src_dir=True,
            has_tests_dir=True,
            has_config_dir=True
        ),
        testing_info=TestingInfo(
            has_unit_tests=True,
            has_integration_tests=True,
            test_frameworks=["go-test"]
        ),
        security_info=SecurityInfo(
            has_security_tools=True,
            has_env_files=True,
            authentication_methods=["jwt"]
        ),
        deployment_info=DeploymentInfo(
            containerized=True,
            container_tools=["docker", "kubernetes"],
            cloud_platforms=["gcp"],
            ci_cd_tools=["github-actions"],
            infrastructure_as_code=["terraform"]
        )
    )


def create_data_science_project():
    """Create a sample data science project analysis."""
    return AnalysisResult(
        project_path="/projects/ml-pipeline",
        project_type=ProjectType.DATA_SCIENCE,
        languages=LanguageInfo(
            primary_language="python",
            languages={"python": 0.8, "r": 0.15, "sql": 0.05},
            file_extensions={".py", ".ipynb", ".r", ".sql"},
            total_files=65
        ),
        frameworks=[
            FrameworkInfo(
                name="pandas",
                category=FrameworkCategory.ANALYTICS,
                confidence=0.95
            ),
            FrameworkInfo(
                name="scikit-learn",
                category=FrameworkCategory.ANALYTICS,
                confidence=0.9
            ),
            FrameworkInfo(
                name="jupyter",
                category=FrameworkCategory.ANALYTICS,
                confidence=0.85
            )
        ],
        directory_info=DirectoryInfo(
            has_src_dir=True,
            has_tests_dir=True,
            has_docs_dir=True,
            has_scripts_dir=True
        ),
        testing_info=TestingInfo(
            has_unit_tests=True,
            test_frameworks=["pytest"]
        ),
        security_info=SecurityInfo(
            has_env_files=True
        ),
        deployment_info=DeploymentInfo(
            containerized=True,
            container_tools=["docker"]
        )
    )


def demonstrate_tag_generation():
    """Demonstrate tag generation for different project types."""
    generator = TagGenerator()
    
    projects = [
        ("React Frontend Project", create_react_frontend_project()),
        ("Django Backend Project", create_django_backend_project()),
        ("Go Microservice", create_microservice_project()),
        ("Data Science Project", create_data_science_project()),
    ]
    
    print("🏷️  Intelligent Tag Generation Demonstration")
    print("=" * 50)
    
    for project_name, analysis in projects:
        print(f"\n📁 {project_name}")
        print("-" * 30)
        
        # Generate tags
        tags = generator.generate_tags(analysis)
        
        # Display results
        print(f"Primary Language: {analysis.languages.primary_language}")
        print(f"Project Type: {analysis.project_type.value}")
        print(f"Frameworks: {', '.join([fw.name for fw in analysis.frameworks])}")
        print(f"Generated Tags ({len(tags)}): {', '.join(tags)}")
        
        # Show explanations for first few tags
        explanations = generator.get_tag_explanations(tags[:5], analysis)
        print("\nTag Explanations:")
        for tag, explanation in explanations.items():
            print(f"  • {tag}: {explanation}")


def demonstrate_tag_mapping_examples():
    """Show examples of framework-to-tag mappings."""
    from airules.analyzer.tag_rules import FRAMEWORK_TAG_MAPPING
    
    print("\n\n🔗 Framework-to-Tag Mapping Examples")
    print("=" * 40)
    
    example_frameworks = [
        "react", "django", "express", "spring-boot", 
        "docker", "kubernetes", "pytest", "jest"
    ]
    
    for framework in example_frameworks:
        if framework in FRAMEWORK_TAG_MAPPING:
            tags = FRAMEWORK_TAG_MAPPING[framework]
            print(f"\n{framework} → {', '.join(tags)}")


if __name__ == "__main__":
    demonstrate_tag_generation()
    demonstrate_tag_mapping_examples()