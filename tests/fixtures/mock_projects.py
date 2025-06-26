"""Mock project structures for testing the auto feature."""

import json
from pathlib import Path
from typing import Dict, List, Union


def create_python_project(base_path: Path, project_name: str = "test_project") -> Path:
    """Create a mock Python project structure."""
    project_path = base_path / project_name
    project_path.mkdir(parents=True, exist_ok=True)

    # Create requirements.txt
    requirements = [
        "flask==2.3.2",
        "requests==2.31.0",
        "pytest==7.4.0",
        "black==23.3.0",
        "flake8==6.0.0",
    ]
    (project_path / "requirements.txt").write_text("\n".join(requirements))

    # Create setup.py
    setup_py = """from setuptools import setup, find_packages

setup(
    name="test_project",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "flask>=2.3.0",
        "requests>=2.31.0",
    ],
    extras_require={
        "dev": ["pytest", "black", "flake8"],
    },
)"""
    (project_path / "setup.py").write_text(setup_py)

    # Create pyproject.toml
    pyproject_toml = """[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "test_project"
version = "0.1.0"
description = "A test project"
dependencies = [
    "flask>=2.3.0",
    "requests>=2.31.0",
]

[project.optional-dependencies]
dev = ["pytest", "black", "flake8"]

[tool.black]
line-length = 88
target-version = ['py38']

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
"""
    (project_path / "pyproject.toml").write_text(pyproject_toml)

    # Create main module
    main_module = project_path / "src" / project_name
    main_module.mkdir(parents=True, exist_ok=True)
    (main_module / "__init__.py").write_text("")

    main_py = '''"""Main module for test project."""

from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, World!"

if __name__ == "__main__":
    app.run(debug=True)
'''
    (main_module / "main.py").write_text(main_py)

    # Create tests directory
    tests_dir = project_path / "tests"
    tests_dir.mkdir(exist_ok=True)
    (tests_dir / "__init__.py").write_text("")

    test_main = '''"""Tests for main module."""

import pytest
from src.test_project.main import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_hello(client):
    """Test hello endpoint."""
    rv = client.get('/')
    assert rv.data == b'Hello, World!'
'''
    (tests_dir / "test_main.py").write_text(test_main)

    # Create .gitignore
    gitignore = """__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.pytest_cache/
.coverage
htmlcov/
.tox/
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/
.mypy_cache/
.dmypy.json
dmypy.json
"""
    (project_path / ".gitignore").write_text(gitignore)

    return project_path


def create_django_project(base_path: Path, project_name: str = "django_test") -> Path:
    """Create a mock Django project structure."""
    project_path = base_path / project_name
    project_path.mkdir(parents=True, exist_ok=True)

    # Create requirements.txt
    requirements = [
        "Django==4.2.3",
        "django-rest-framework==3.14.0",
        "psycopg2-binary==2.9.7",
        "celery==5.3.1",
        "redis==4.6.0",
        "pytest-django==4.5.2",
    ]
    (project_path / "requirements.txt").write_text("\n".join(requirements))

    # Create manage.py
    manage_py = '''#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_test.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
'''
    (project_path / "manage.py").write_text(manage_py)

    # Create Django settings
    settings_dir = project_path / project_name
    settings_dir.mkdir(exist_ok=True)
    (settings_dir / "__init__.py").write_text("")

    settings_py = '''"""Django settings for django_test project."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'test-secret-key'
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'django_test.urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'test_db',
        'USER': 'test_user',
        'PASSWORD': 'test_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

STATIC_URL = '/static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
'''
    (settings_dir / "settings.py").write_text(settings_py)

    # Create core app
    core_dir = project_path / "core"
    core_dir.mkdir(exist_ok=True)
    (core_dir / "__init__.py").write_text("")

    models_py = '''"""Core models."""

from django.db import models

class User(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
'''
    (core_dir / "models.py").write_text(models_py)

    return project_path


def create_react_project(base_path: Path, project_name: str = "react_test") -> Path:
    """Create a mock React project structure."""
    project_path = base_path / project_name
    project_path.mkdir(parents=True, exist_ok=True)

    # Create package.json
    package_json = {
        "name": "react_test",
        "version": "0.1.0",
        "private": True,
        "dependencies": {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "react-router-dom": "^6.14.1",
            "axios": "^1.4.0",
            "@mui/material": "^5.14.1",
            "@emotion/react": "^11.11.1",
            "@emotion/styled": "^11.11.0",
        },
        "devDependencies": {
            "@testing-library/jest-dom": "^5.16.5",
            "@testing-library/react": "^13.4.0",
            "@testing-library/user-event": "^14.4.3",
            "@types/react": "^18.2.15",
            "@types/react-dom": "^18.2.7",
            "eslint": "^8.45.0",
            "prettier": "^3.0.0",
            "typescript": "^5.1.6",
        },
        "scripts": {
            "start": "react-scripts start",
            "build": "react-scripts build",
            "test": "react-scripts test",
            "eject": "react-scripts eject",
        },
    }
    (project_path / "package.json").write_text(json.dumps(package_json, indent=2))

    # Create tsconfig.json
    tsconfig = {
        "compilerOptions": {
            "target": "es5",
            "lib": ["dom", "dom.iterable", "esnext"],
            "allowJs": True,
            "skipLibCheck": True,
            "esModuleInterop": True,
            "allowSyntheticDefaultImports": True,
            "strict": True,
            "forceConsistentCasingInFileNames": True,
            "module": "esnext",
            "moduleResolution": "node",
            "resolveJsonModule": True,
            "isolatedModules": True,
            "noEmit": True,
            "jsx": "react-jsx",
        },
        "include": ["src"],
    }
    (project_path / "tsconfig.json").write_text(json.dumps(tsconfig, indent=2))

    # Create src directory
    src_dir = project_path / "src"
    src_dir.mkdir(exist_ok=True)

    # Create App.tsx
    app_tsx = """import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Home from './components/Home';
import About from './components/About';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/about" element={<About />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
"""
    (src_dir / "App.tsx").write_text(app_tsx)

    # Create components directory
    components_dir = src_dir / "components"
    components_dir.mkdir(exist_ok=True)

    home_tsx = """import React from 'react';
import { Container, Typography, Button } from '@mui/material';
import { Link } from 'react-router-dom';

const Home: React.FC = () => {
  return (
    <Container maxWidth="sm" sx={{ mt: 4 }}>
      <Typography variant="h2" component="h1" gutterBottom>
        Welcome to React Test
      </Typography>
      <Typography variant="body1" paragraph>
        This is a test React application with Material-UI and TypeScript.
      </Typography>
      <Button component={Link} to="/about" variant="contained">
        Learn More
      </Button>
    </Container>
  );
};

export default Home;
"""
    (components_dir / "Home.tsx").write_text(home_tsx)

    return project_path


def create_nextjs_project(base_path: Path, project_name: str = "nextjs_test") -> Path:
    """Create a mock Next.js project structure."""
    project_path = base_path / project_name
    project_path.mkdir(parents=True, exist_ok=True)

    # Create package.json
    package_json = {
        "name": "nextjs_test",
        "version": "0.1.0",
        "private": True,
        "scripts": {
            "dev": "next dev",
            "build": "next build",
            "start": "next start",
            "lint": "next lint",
        },
        "dependencies": {
            "next": "13.4.7",
            "react": "18.2.0",
            "react-dom": "18.2.0",
            "@next/font": "13.4.7",
            "tailwindcss": "^3.3.3",
            "autoprefixer": "^10.4.14",
            "postcss": "^8.4.24",
        },
        "devDependencies": {
            "typescript": "^5.1.6",
            "@types/react": "18.2.15",
            "@types/node": "20.4.5",
            "eslint": "8.45.0",
            "eslint-config-next": "13.4.7",
        },
    }
    (project_path / "package.json").write_text(json.dumps(package_json, indent=2))

    # Create next.config.js
    next_config = """/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
}

module.exports = nextConfig
"""
    (project_path / "next.config.js").write_text(next_config)

    # Create app directory (Next.js 13+ app router)
    app_dir = project_path / "app"
    app_dir.mkdir(exist_ok=True)

    # Create layout.tsx
    layout_tsx = """import './globals.css'
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'Next.js Test App',
  description: 'A test Next.js application',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
"""
    (app_dir / "layout.tsx").write_text(layout_tsx)

    # Create page.tsx
    page_tsx = """import Link from 'next/link'

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm">
        <h1 className="text-4xl font-bold mb-4">
          Welcome to Next.js Test!
        </h1>
        <p className="text-xl mb-8">
          This is a test Next.js application with TypeScript and Tailwind CSS.
        </p>
        <Link href="/about" className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
          Learn More
        </Link>
      </div>
    </main>
  )
}
"""
    (app_dir / "page.tsx").write_text(page_tsx)

    # Create tailwind.config.js
    tailwind_config = """/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
"""
    (project_path / "tailwind.config.js").write_text(tailwind_config)

    return project_path


def create_rust_project(base_path: Path, project_name: str = "rust_test") -> Path:
    """Create a mock Rust project structure."""
    project_path = base_path / project_name
    project_path.mkdir(parents=True, exist_ok=True)

    # Create Cargo.toml
    cargo_toml = """[package]
name = "rust_test"
version = "0.1.0"
edition = "2021"

[dependencies]
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
tokio = { version = "1.0", features = ["full"] }
reqwest = { version = "0.11", features = ["json"] }
clap = { version = "4.0", features = ["derive"] }
anyhow = "1.0"
thiserror = "1.0"

[dev-dependencies]
tokio-test = "0.4"
"""
    (project_path / "Cargo.toml").write_text(cargo_toml)

    # Create src directory
    src_dir = project_path / "src"
    src_dir.mkdir(exist_ok=True)

    # Create main.rs
    main_rs = """use anyhow::Result;
use clap::Parser;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Name of the person to greet
    #[arg(short, long)]
    name: String,

    /// Number of times to greet
    #[arg(short, long, default_value_t = 1)]
    count: u8,
}

#[derive(Serialize, Deserialize, Debug)]
struct Config {
    app_name: String,
    version: String,
    features: HashMap<String, bool>,
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();

    let config = Config {
        app_name: "Rust Test".to_string(),
        version: "0.1.0".to_string(),
        features: HashMap::from([
            ("async".to_string(), true),
            ("json".to_string(), true),
        ]),
    };

    println!("Starting {} v{}", config.app_name, config.version);

    for _ in 0..args.count {
        println!("Hello {}!", args.name);
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_config_creation() {
        let config = Config {
            app_name: "Test".to_string(),
            version: "1.0.0".to_string(),
            features: HashMap::new(),
        };

        assert_eq!(config.app_name, "Test");
        assert_eq!(config.version, "1.0.0");
    }
}
"""
    (src_dir / "main.rs").write_text(main_rs)

    # Create lib.rs
    lib_rs = """//! A simple Rust library for testing

use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct User {
    pub id: u64,
    pub name: String,
    pub email: String,
    pub active: bool,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct UserManager {
    users: HashMap<u64, User>,
    next_id: u64,
}

impl UserManager {
    pub fn new() -> Self {
        Self {
            users: HashMap::new(),
            next_id: 1,
        }
    }

    pub fn add_user(&mut self, name: String, email: String) -> Result<u64> {
        let user = User {
            id: self.next_id,
            name,
            email,
            active: true,
        };

        self.users.insert(self.next_id, user);
        let id = self.next_id;
        self.next_id += 1;

        Ok(id)
    }

    pub fn get_user(&self, id: u64) -> Option<&User> {
        self.users.get(&id)
    }

    pub fn list_users(&self) -> Vec<&User> {
        self.users.values().collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_user_manager() {
        let mut manager = UserManager::new();

        let id = manager.add_user("John Doe".to_string(), "john@example.com".to_string()).unwrap();
        assert_eq!(id, 1);

        let user = manager.get_user(id).unwrap();
        assert_eq!(user.name, "John Doe");
        assert_eq!(user.email, "john@example.com");
        assert!(user.active);
    }
}
"""
    (src_dir / "lib.rs").write_text(lib_rs)

    return project_path


def create_fastapi_project(base_path: Path, project_name: str = "fastapi_test") -> Path:
    """Create a mock FastAPI project structure."""
    project_path = base_path / project_name
    project_path.mkdir(parents=True, exist_ok=True)

    # Create requirements.txt
    requirements = [
        "fastapi==0.100.0",
        "uvicorn[standard]==0.23.1",
        "pydantic==2.0.3",
        "sqlalchemy==2.0.19",
        "alembic==1.11.1",
        "python-multipart==0.0.6",
        "pytest==7.4.0",
        "httpx==0.24.1",
        "pytest-asyncio==0.21.1",
    ]
    (project_path / "requirements.txt").write_text("\n".join(requirements))

    # Create main.py
    main_py = '''"""FastAPI application main module."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(
    title="FastAPI Test",
    description="A test FastAPI application",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class UserCreate(BaseModel):
    name: str
    email: str

class User(BaseModel):
    id: int
    name: str
    email: str
    active: bool = True

# In-memory storage for demo
users_db: List[User] = []
next_id = 1

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Hello World from FastAPI!"}

@app.get("/users", response_model=List[User])
async def get_users():
    """Get all users."""
    return users_db

@app.post("/users", response_model=User)
async def create_user(user: UserCreate):
    """Create a new user."""
    global next_id
    new_user = User(
        id=next_id,
        name=user.name,
        email=user.email,
    )
    users_db.append(new_user)
    next_id += 1
    return new_user

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    """Get a specific user."""
    for user in users_db:
        if user.id == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
    (project_path / "main.py").write_text(main_py)

    # Create tests directory
    tests_dir = project_path / "tests"
    tests_dir.mkdir(exist_ok=True)
    (tests_dir / "__init__.py").write_text("")

    # Create test_main.py
    test_main = '''"""Tests for FastAPI application."""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World from FastAPI!"}

def test_create_user():
    """Test user creation."""
    user_data = {"name": "John Doe", "email": "john@example.com"}
    response = client.post("/users", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["email"] == "john@example.com"
    assert data["active"] is True
    assert "id" in data

def test_get_users():
    """Test getting all users."""
    response = client.get("/users")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
'''
    (tests_dir / "test_main.py").write_text(test_main)

    return project_path
