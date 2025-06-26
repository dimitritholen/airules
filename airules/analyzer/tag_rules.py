"""Tag mapping rules and patterns for framework and technology detection."""

from typing import Dict, List

from .data_models import ProjectType

# Core framework-to-tags mappings
FRAMEWORK_TAG_MAPPING: Dict[str, List[str]] = {
    # Frontend Frameworks
    "react": ["components", "jsx", "hooks", "virtual-dom", "state-management"],
    "vue": ["components", "reactive", "single-file-components", "vue-router"],
    "angular": ["components", "typescript", "dependency-injection", "rxjs", "cli"],
    "svelte": ["components", "compile-time", "reactive", "minimal-bundle"],
    "next.js": ["react", "ssr", "routing", "full-stack", "api-routes"],
    "nuxt.js": ["vue", "ssr", "routing", "full-stack", "auto-imports"],
    "gatsby": ["react", "static-site", "graphql", "performance", "pwa"],
    "astro": ["static-site", "components", "islands", "performance"],
    # Backend Frameworks
    "express": ["node.js", "middleware", "rest-api", "web-server"],
    "fastapi": ["python", "async", "rest-api", "openapi", "type-hints"],
    "django": ["python", "orm", "mvc", "rest-api", "admin-panel"],
    "flask": ["python", "microframework", "web-server", "rest-api"],
    "spring-boot": ["java", "dependency-injection", "rest-api", "microservices"],
    "rails": ["ruby", "mvc", "orm", "convention-over-configuration"],
    "laravel": ["php", "mvc", "orm", "artisan", "eloquent"],
    "asp.net": ["c#", "mvc", "web-api", "entity-framework"],
    "gin": ["go", "web-framework", "middleware", "rest-api"],
    "fiber": ["go", "web-framework", "fast", "express-inspired"],
    # Mobile Frameworks
    "react-native": ["mobile", "cross-platform", "react", "native-modules"],
    "flutter": ["mobile", "cross-platform", "dart", "widgets"],
    "ionic": ["mobile", "hybrid", "web-technologies", "capacitor"],
    "xamarin": ["mobile", "cross-platform", "c#", "native-api"],
    # Desktop Frameworks
    "electron": ["desktop", "cross-platform", "web-technologies", "node.js"],
    "tauri": ["desktop", "rust", "web-frontend", "lightweight"],
    "qt": ["desktop", "cross-platform", "c++", "gui"],
    "tkinter": ["desktop", "python", "gui", "built-in"],
    # Databases
    "postgresql": ["database", "relational", "sql", "acid"],
    "mysql": ["database", "relational", "sql", "web-development"],
    "mongodb": ["database", "nosql", "document", "json"],
    "redis": ["database", "in-memory", "cache", "key-value"],
    "sqlite": ["database", "embedded", "sql", "lightweight"],
    "elasticsearch": ["search", "analytics", "distributed", "full-text"],
    # Testing Frameworks
    "jest": ["testing", "unit-tests", "mocking", "javascript"],
    "pytest": ["testing", "unit-tests", "fixtures", "python"],
    "mocha": ["testing", "unit-tests", "javascript", "flexible"],
    "cypress": ["testing", "e2e", "browser", "ui-testing"],
    "selenium": ["testing", "e2e", "cross-browser", "automation"],
    "junit": ["testing", "unit-tests", "java", "assertions"],
    "rspec": ["testing", "bdd", "ruby", "readable"],
    # Build Tools and Bundlers
    "webpack": ["bundler", "module-federation", "asset-optimization"],
    "vite": ["bundler", "dev-server", "fast", "esbuild"],
    "rollup": ["bundler", "es-modules", "tree-shaking"],
    "parcel": ["bundler", "zero-config", "web-applications"],
    "gulp": ["task-runner", "streaming", "build-automation"],
    "grunt": ["task-runner", "configuration", "build-automation"],
    # State Management
    "redux": ["state-management", "predictable", "flux-pattern"],
    "vuex": ["state-management", "vue", "centralized"],
    "mobx": ["state-management", "reactive", "observable"],
    "zustand": ["state-management", "lightweight", "react"],
    # Styling
    "tailwindcss": ["css", "utility-first", "responsive", "customizable"],
    "bootstrap": ["css", "responsive", "components", "grid-system"],
    "sass": ["css", "preprocessor", "variables", "nesting"],
    "styled-components": ["css-in-js", "react", "component-scoped"],
    # DevOps and Deployment
    "docker": ["containerization", "deployment", "microservices"],
    "kubernetes": ["orchestration", "containers", "scalability"],
    "terraform": ["infrastructure-as-code", "cloud", "provisioning"],
    "ansible": ["configuration-management", "automation", "idempotent"],
    "jenkins": ["ci-cd", "automation", "pipelines"],
    "github-actions": ["ci-cd", "workflows", "automation"],
    # Cloud Platforms
    "aws": ["cloud", "scalability", "managed-services"],
    "azure": ["cloud", "microsoft", "enterprise"],
    "gcp": ["cloud", "google", "machine-learning"],
    "vercel": ["deployment", "frontend", "serverless"],
    "netlify": ["deployment", "jamstack", "cdn"],
    # Authentication
    "auth0": ["authentication", "sso", "oauth", "managed-service"],
    "firebase-auth": ["authentication", "google", "social-login"],
    "passport": ["authentication", "node.js", "strategies"],
    "oauth": ["authentication", "authorization", "third-party"],
    # Monitoring and Analytics
    "sentry": ["error-tracking", "monitoring", "debugging"],
    "datadog": ["monitoring", "apm", "infrastructure"],
    "new-relic": ["monitoring", "performance", "apm"],
    "google-analytics": ["analytics", "web-tracking", "insights"],
}

# Project type specific tags
PROJECT_TYPE_TAGS: Dict[ProjectType, List[str]] = {
    ProjectType.WEB_FRONTEND: ["frontend", "browser", "user-interface", "responsive"],
    ProjectType.WEB_BACKEND: ["backend", "server", "api", "database"],
    ProjectType.FULLSTACK: ["fullstack", "frontend", "backend", "api"],
    ProjectType.MOBILE: ["mobile", "ios", "android", "native"],
    ProjectType.DESKTOP: ["desktop", "gui", "native", "cross-platform"],
    ProjectType.CLI: ["cli", "command-line", "terminal", "automation"],
    ProjectType.LIBRARY: ["library", "reusable", "module", "package"],
    ProjectType.MICROSERVICE: ["microservices", "distributed", "api", "scalable"],
    ProjectType.MONOLITH: ["monolith", "single-deployment", "integrated"],
    ProjectType.DATA_SCIENCE: ["data-science", "analytics", "visualization", "jupyter"],
    ProjectType.MACHINE_LEARNING: ["machine-learning", "ai", "models", "training"],
    ProjectType.DEVOPS: ["devops", "automation", "deployment", "infrastructure"],
    ProjectType.GAME: ["game", "graphics", "real-time", "performance"],
}

# Language-specific tags
LANGUAGE_TAGS: Dict[str, List[str]] = {
    "javascript": ["javascript", "dynamic", "event-driven", "web"],
    "typescript": ["typescript", "static-typing", "javascript", "type-safety"],
    "python": ["python", "readable", "dynamic", "interpreted"],
    "java": ["java", "object-oriented", "jvm", "enterprise"],
    "c#": ["csharp", "object-oriented", "dotnet", "microsoft"],
    "go": ["golang", "concurrent", "compiled", "google"],
    "rust": ["rust", "memory-safe", "performance", "systems"],
    "c++": ["cpp", "performance", "systems", "manual-memory"],
    "ruby": ["ruby", "dynamic", "readable", "web"],
    "php": ["php", "web", "server-side", "dynamic"],
    "swift": ["swift", "ios", "macos", "apple"],
    "kotlin": ["kotlin", "android", "jvm", "interoperable"],
    "dart": ["dart", "flutter", "google", "optimized"],
    "scala": ["scala", "functional", "jvm", "concurrent"],
    "r": ["r", "statistics", "data-analysis", "visualization"],
    "sql": ["sql", "database", "queries", "relational"],
}

# Context-aware tag generation patterns
CONTEXT_PATTERNS: Dict[str, List[str]] = {
    # File patterns that suggest specific tags
    "test_files": ["testing", "quality-assurance", "unit-tests"],
    "api_routes": ["rest-api", "endpoints", "web-services"],
    "database_migrations": ["database", "schema", "versioning"],
    "docker_files": ["containerization", "deployment", "docker"],
    "ci_cd_configs": ["ci-cd", "automation", "deployment"],
    "security_configs": ["security", "authentication", "authorization"],
    "documentation": ["documentation", "readme", "guides"],
    "configuration": ["configuration", "settings", "environment"],
    "assets": ["assets", "static-files", "resources"],
    "translations": ["i18n", "localization", "multilingual"],
}

# Directory structure tags
DIRECTORY_TAGS: Dict[str, List[str]] = {
    "src": ["source-code", "organized"],
    "lib": ["library", "modules"],
    "tests": ["testing", "quality-assurance"],
    "docs": ["documentation", "guides"],
    "scripts": ["automation", "utilities"],
    "config": ["configuration", "settings"],
    "assets": ["assets", "static-files"],
    "static": ["static-files", "public"],
    "templates": ["templates", "views"],
    "migrations": ["database", "schema-evolution"],
    "components": ["components", "modular"],
    "services": ["services", "business-logic"],
    "utils": ["utilities", "helpers"],
    "middleware": ["middleware", "request-processing"],
    "models": ["data-models", "entities"],
    "controllers": ["controllers", "request-handlers"],
    "views": ["views", "presentation"],
    "routes": ["routing", "url-mapping"],
}

# Tag priorities for ranking
TAG_PRIORITIES: Dict[str, int] = {
    # High priority - core technology tags
    "react": 10,
    "vue": 10,
    "angular": 10,
    "django": 10,
    "flask": 10,
    "express": 10,
    "fastapi": 10,
    "spring-boot": 10,
    "next.js": 10,
    # Medium-high priority - important architectural tags
    "rest-api": 9,
    "microservices": 9,
    "database": 9,
    "testing": 9,
    "containerization": 9,
    "ci-cd": 9,
    "authentication": 9,
    # Medium priority - development practices
    "components": 8,
    "typescript": 8,
    "unit-tests": 8,
    "security": 8,
    "performance": 8,
    "responsive": 8,
    "scalable": 8,
    # Lower priority - supplementary tags
    "utilities": 6,
    "configuration": 6,
    "documentation": 6,
    "assets": 5,
    "static-files": 5,
    # Default priority for unspecified tags
}

# Tags that should be excluded in certain contexts
EXCLUSION_RULES: Dict[str, List[str]] = {
    "mobile": ["browser", "responsive"],  # Mobile apps don't need browser-specific tags
    "api": ["frontend", "user-interface"],  # API-only projects don't need UI tags
    "library": ["deployment", "hosting"],  # Libraries don't need deployment tags
    "cli": ["web", "browser", "responsive"],  # CLI tools don't need web tags
}

# Tags that should be grouped together
TAG_GROUPS: Dict[str, List[str]] = {
    "web-development": ["html", "css", "javascript", "web"],
    "data-processing": ["data-science", "analytics", "etl", "big-data"],
    "security": ["authentication", "authorization", "encryption", "oauth"],
    "performance": ["optimization", "caching", "lazy-loading", "minification"],
    "testing": ["unit-tests", "integration-tests", "e2e", "tdd", "bdd"],
}

# Maximum recommended tags per project
MAX_TAGS_PER_PROJECT = 15
MIN_TAGS_PER_PROJECT = 3

# Confidence thresholds for including tags
MIN_CONFIDENCE_THRESHOLD = 0.3
HIGH_CONFIDENCE_THRESHOLD = 0.8
