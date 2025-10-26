#!/usr/bin/env python3
"""
Test pipeline for simulating merge conflicts to test merj pull functionality.
Creates temporary git repositories with controlled conflicts for testing.
"""

import os
import sys
import json
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import time
from datetime import datetime

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'rag_pipeline'))

# Set API key for Voyage
os.environ["VOYAGE_API_KEY"] = os.environ.get("VOYAGE_API_KEY", "pa-XpJmKf_6HucjcZRGDueQzIVsHq3LHMsEU4E1UStG5wB")


class MergeConflictSimulator:
    """Simulates merge conflicts for testing the merj tool."""

    def __init__(self, base_dir: str = None):
        """Initialize simulator with optional base directory."""
        if base_dir:
            self.base_dir = Path(base_dir)
            self.base_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.temp_dir = tempfile.mkdtemp(prefix="merj_test_")
            self.base_dir = Path(self.temp_dir)

        self.test_repo_path = None
        self.remote_repo_path = None
        self.conflicts_created = []

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup."""
        self.cleanup()

    def cleanup(self):
        """Clean up temporary directories."""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            print(f"🧹 Cleaned up temporary directory: {self.temp_dir}")

    def run_git(self, cmd: str, cwd: str = None) -> Tuple[bool, str, str]:
        """Run git command and return success, stdout, stderr."""
        if cwd is None:
            cwd = self.test_repo_path

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    def create_test_repo(self, name: str = "test_repo") -> Path:
        """Create a new git repository for testing."""
        repo_path = self.base_dir / name
        repo_path.mkdir(parents=True, exist_ok=True)
        self.test_repo_path = repo_path

        # Initialize git repo
        self.run_git("git init")
        self.run_git("git config user.email 'test@example.com'")
        self.run_git("git config user.name 'Test User'")

        print(f"📁 Created test repository at: {repo_path}")
        return repo_path

    def create_remote_repo(self, name: str = "remote_repo") -> Path:
        """Create a bare git repository to act as a remote."""
        remote_path = self.base_dir / name
        remote_path.mkdir(parents=True, exist_ok=True)
        self.remote_repo_path = remote_path

        # Initialize bare repo
        success, _, _ = self.run_git("git init --bare", cwd=str(remote_path))
        if success:
            print(f"📡 Created remote repository at: {remote_path}")
        return remote_path

    def setup_remote_and_clone(self, remote_name: str = "remote", local_name: str = "local") -> Tuple[Path, Path]:
        """Set up a remote repository and clone it locally."""
        # Create bare remote repo
        remote_path = self.create_remote_repo(remote_name)

        # Clone to create local repo
        local_path = self.base_dir / local_name
        clone_cmd = f"git clone {remote_path} {local_path}"
        success, _, _ = self.run_git(clone_cmd, cwd=str(self.base_dir))

        if success:
            self.test_repo_path = local_path
            # Configure git in the cloned repo
            self.run_git("git config user.email 'test@example.com'")
            self.run_git("git config user.name 'Test User'")
            print(f"📋 Cloned repository to: {local_path}")
        else:
            print(f"❌ Failed to clone repository")

        return remote_path, local_path

    def push_to_remote(self, branch: str = None) -> bool:
        """Push current branch to remote."""
        if branch:
            cmd = f"git push origin {branch}"
        else:
            cmd = "git push"

        success, _, _ = self.run_git(cmd)
        return success

    def simulate_divergent_changes(self) -> bool:
        """Create divergent changes between local and remote to cause conflicts on pull."""
        print("\n🔀 Creating divergent changes between local and remote...")

        # First, create an initial file and push to remote
        base_content = '''def calculate_price(items):
    """Calculate total price."""
    total = 0
    for item in items:
        total += item['price']
    return total
'''
        self.write_file("pricing.py", base_content, "Initial pricing function")
        self.run_git("git push -u origin main")
        print("✓ Pushed initial version to remote")

        # Now make changes directly in the remote (simulate another developer)
        # We'll do this by creating another clone, making changes, and pushing
        temp_clone = self.base_dir / "temp_remote_changes"
        clone_cmd = f"git clone {self.remote_repo_path} {temp_clone}"
        success, _, _ = self.run_git(clone_cmd, cwd=str(self.base_dir))

        if success:
            # Make changes in the temporary clone
            remote_content = '''def calculate_price(items, tax_rate=0.08):
    """Calculate total price with tax."""
    subtotal = 0
    for item in items:
        subtotal += item['price'] * item.get('quantity', 1)

    tax = subtotal * tax_rate
    return subtotal + tax

def apply_discount(total, discount_percent):
    """Apply discount to total."""
    return total * (1 - discount_percent)
'''
            temp_file = temp_clone / "pricing.py"
            with open(temp_file, 'w') as f:
                f.write(remote_content)

            # Configure git first, then commit and push from temp clone
            self.run_git("git config user.email 'remote@example.com'", cwd=str(temp_clone))
            self.run_git("git config user.name 'Remote User'", cwd=str(temp_clone))
            self.run_git("git add .", cwd=str(temp_clone))
            success2, _, _ = self.run_git('git commit -m "Add tax calculation and discount function"', cwd=str(temp_clone))
            if success2:
                success3, _, stderr = self.run_git("git push", cwd=str(temp_clone))
                if not success3:
                    print(f"⚠️  Failed to push from temp clone: {stderr}")
            print("✓ Pushed remote changes (tax and discount)")

            # Clean up temp clone
            shutil.rmtree(temp_clone, ignore_errors=True)

        # Now make local changes (without pulling)
        local_content = '''def calculate_price(items):
    """Calculate total price with shipping."""
    total = 0
    for item in items:
        price = item['price']
        total += price

    # Add shipping
    if total < 50:
        shipping = 9.99
    else:
        shipping = 0

    return total + shipping

def validate_items(items):
    """Validate items before pricing."""
    for item in items:
        if 'price' not in item:
            return False
    return True
'''
        self.write_file("pricing.py", local_content, "Add shipping calculation and validation")
        print("✓ Made local changes (shipping and validation)")

        return True

    def write_file(self, filename: str, content: str, commit_msg: str = None):
        """Write a file and optionally commit it."""
        file_path = self.test_repo_path / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w') as f:
            f.write(content)

        if commit_msg:
            self.run_git(f"git add {filename}")
            self.run_git(f'git commit -m "{commit_msg}"')

    def create_branch(self, branch_name: str, checkout: bool = True) -> bool:
        """Create and optionally checkout a new branch."""
        success, _, _ = self.run_git(f"git branch {branch_name}")
        if success and checkout:
            success, _, _ = self.run_git(f"git checkout {branch_name}")
        return success

    def simulate_python_conflict(self) -> Dict:
        """Simulate a merge conflict in a Python file."""
        print("\n🐍 Simulating Python merge conflict...")

        # Create base version
        base_content = '''def calculate_total(items):
    """Calculate total price of items."""
    total = 0
    for item in items:
        total += item['price']
    return total

def process_order(order_data):
    """Process an order."""
    items = order_data.get('items', [])
    total = calculate_total(items)
    return {
        'order_id': order_data['id'],
        'total': total,
        'status': 'pending'
    }
'''
        self.write_file("order_processor.py", base_content, "Initial order processor")

        # Create feature branch with changes
        self.create_branch("feature-branch")
        feature_content = '''def calculate_total(items):
    """Calculate total price of items with tax."""
    subtotal = 0
    for item in items:
        subtotal += item['price'] * item.get('quantity', 1)

    # Add 10% tax
    tax = subtotal * 0.10
    return subtotal + tax

def process_order(order_data):
    """Process an order with validation."""
    if 'id' not in order_data:
        raise ValueError("Order must have an ID")

    items = order_data.get('items', [])
    total = calculate_total(items)
    return {
        'order_id': order_data['id'],
        'total': round(total, 2),
        'status': 'validated',
        'timestamp': datetime.now().isoformat()
    }

def validate_items(items):
    """Validate order items."""
    for item in items:
        if 'price' not in item:
            return False
    return True
'''
        self.write_file("order_processor.py", feature_content, "Add tax calculation and validation")

        # Go back to main and make different changes
        self.run_git("git checkout main")
        main_content = '''def calculate_total(items):
    """Calculate total price with discount."""
    total = 0
    for item in items:
        price = item['price']
        discount = item.get('discount', 0)
        total += price * (1 - discount)
    return total

def process_order(order_data):
    """Process an order with shipping."""
    items = order_data.get('items', [])
    subtotal = calculate_total(items)

    # Add shipping cost
    shipping = 5.99 if subtotal < 50 else 0
    total = subtotal + shipping

    return {
        'order_id': order_data['id'],
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total,
        'status': 'processing'
    }

def calculate_shipping(subtotal):
    """Calculate shipping based on subtotal."""
    if subtotal < 25:
        return 9.99
    elif subtotal < 50:
        return 5.99
    else:
        return 0
'''
        self.write_file("order_processor.py", main_content, "Add discount and shipping calculation")

        # Attempt merge to create conflict
        success, stdout, stderr = self.run_git("git merge feature-branch")

        conflict_info = {
            'type': 'python',
            'file': 'order_processor.py',
            'branches': ['main', 'feature-branch'],
            'has_conflict': not success,
            'description': 'Conflict between tax/validation vs discount/shipping implementations'
        }

        if not success:
            print("✅ Successfully created Python conflict")
            self.conflicts_created.append(conflict_info)
        else:
            print("⚠️  No conflict created (files merged cleanly)")

        return conflict_info

    def simulate_javascript_conflict(self) -> Dict:
        """Simulate a merge conflict in a JavaScript file."""
        print("\n🟨 Simulating JavaScript merge conflict...")

        # Reset to clean state
        self.run_git("git reset --hard HEAD")
        self.run_git("git checkout main")

        # Create base version
        base_content = '''class UserService {
    constructor(database) {
        this.db = database;
        this.users = [];
    }

    async createUser(userData) {
        const user = {
            id: Date.now(),
            name: userData.name,
            email: userData.email,
            created: new Date()
        };

        this.users.push(user);
        return user;
    }

    async getUser(id) {
        return this.users.find(u => u.id === id);
    }
}

module.exports = UserService;
'''
        self.write_file("services/user_service.js", base_content, "Initial user service")

        # Create api-update branch
        self.create_branch("api-update")
        api_content = '''class UserService {
    constructor(database, cache) {
        this.db = database;
        this.cache = cache;
        this.users = new Map();
    }

    async createUser(userData) {
        // Validate required fields
        if (!userData.email || !userData.name) {
            throw new Error('Email and name are required');
        }

        const user = {
            id: crypto.randomUUID(),
            name: userData.name,
            email: userData.email.toLowerCase(),
            role: userData.role || 'user',
            created: new Date(),
            lastLogin: null
        };

        this.users.set(user.id, user);
        await this.cache.set(`user:${user.id}`, user);
        return user;
    }

    async getUser(id) {
        // Check cache first
        const cached = await this.cache.get(`user:${id}`);
        if (cached) return cached;

        return this.users.get(id);
    }

    async updateUser(id, updates) {
        const user = await this.getUser(id);
        if (!user) throw new Error('User not found');

        Object.assign(user, updates);
        this.users.set(id, user);
        await this.cache.set(`user:${id}`, user);
        return user;
    }
}

module.exports = UserService;
'''
        self.write_file("services/user_service.js", api_content, "Add caching and validation")

        # Go back to main and make different changes
        self.run_git("git checkout main")
        main_content = '''import { EventEmitter } from 'events';

class UserService extends EventEmitter {
    constructor(database) {
        super();
        this.db = database;
        this.users = [];
    }

    async createUser(userData) {
        const existingUser = this.users.find(u => u.email === userData.email);
        if (existingUser) {
            throw new Error('User already exists');
        }

        const user = {
            id: Date.now().toString(),
            name: userData.name,
            email: userData.email,
            passwordHash: await this.hashPassword(userData.password),
            created: new Date(),
            verified: false
        };

        this.users.push(user);
        this.emit('user:created', user);
        return user;
    }

    async getUser(id) {
        const user = this.users.find(u => u.id === id);
        if (!user) {
            throw new Error(`User ${id} not found`);
        }
        return user;
    }

    async verifyUser(id) {
        const user = await this.getUser(id);
        user.verified = true;
        this.emit('user:verified', user);
        return user;
    }

    async hashPassword(password) {
        // Simplified for demo
        return `hashed_${password}`;
    }
}

export default UserService;
'''
        self.write_file("services/user_service.js", main_content, "Add event emitter and verification")

        # Attempt merge
        success, stdout, stderr = self.run_git("git merge api-update")

        conflict_info = {
            'type': 'javascript',
            'file': 'services/user_service.js',
            'branches': ['main', 'api-update'],
            'has_conflict': not success,
            'description': 'Conflict between caching/validation vs events/verification'
        }

        if not success:
            print("✅ Successfully created JavaScript conflict")
            self.conflicts_created.append(conflict_info)
        else:
            print("⚠️  No conflict created (files merged cleanly)")

        return conflict_info

    def simulate_config_conflict(self) -> Dict:
        """Simulate a merge conflict in a configuration file."""
        print("\n⚙️  Simulating configuration file conflict...")

        # Reset to clean state
        self.run_git("git reset --hard HEAD")
        self.run_git("git checkout main")

        # Create base config
        base_content = '''{
  "name": "test-app",
  "version": "1.0.0",
  "description": "Test application",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "test": "jest"
  },
  "dependencies": {
    "express": "^4.18.0",
    "mongoose": "^6.0.0"
  }
}
'''
        self.write_file("package.json", base_content, "Initial package.json")

        # Create deps-update branch
        self.create_branch("deps-update")
        deps_content = '''{
  "name": "test-app",
  "version": "1.1.0",
  "description": "Test application with updated dependencies",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "dev": "nodemon index.js",
    "test": "jest --coverage",
    "lint": "eslint ."
  },
  "dependencies": {
    "express": "^4.19.0",
    "mongoose": "^7.0.0",
    "dotenv": "^16.0.0",
    "cors": "^2.8.5"
  },
  "devDependencies": {
    "jest": "^29.0.0",
    "eslint": "^8.0.0",
    "nodemon": "^3.0.0"
  }
}
'''
        self.write_file("package.json", deps_content, "Update dependencies and add dev tools")

        # Go back to main and make different changes
        self.run_git("git checkout main")
        scripts_content = '''{
  "name": "test-app",
  "version": "1.0.1",
  "description": "Test application",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "ts-node src/index.ts",
    "test": "jest",
    "docker:build": "docker build -t test-app .",
    "docker:run": "docker run -p 3000:3000 test-app"
  },
  "dependencies": {
    "express": "^4.18.0",
    "mongoose": "^6.5.0",
    "helmet": "^7.0.0",
    "compression": "^1.7.4"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "ts-node": "^10.0.0",
    "@types/express": "^4.17.0"
  }
}
'''
        self.write_file("package.json", scripts_content, "Add TypeScript and Docker support")

        # Attempt merge
        success, stdout, stderr = self.run_git("git merge deps-update")

        conflict_info = {
            'type': 'json',
            'file': 'package.json',
            'branches': ['main', 'deps-update'],
            'has_conflict': not success,
            'description': 'Conflict between dependency updates vs TypeScript/Docker setup'
        }

        if not success:
            print("✅ Successfully created JSON config conflict")
            self.conflicts_created.append(conflict_info)
        else:
            print("⚠️  No conflict created (files merged cleanly)")

        return conflict_info

    def get_conflict_markers(self, filepath: str) -> List[Dict]:
        """Extract conflict markers from a file."""
        file_path = self.test_repo_path / filepath
        if not file_path.exists():
            return []

        with open(file_path, 'r') as f:
            content = f.read()

        markers = []
        lines = content.split('\n')
        in_conflict = False
        conflict_start = -1

        for i, line in enumerate(lines, 1):
            if line.startswith('<<<<<<<'):
                in_conflict = True
                conflict_start = i
            elif line.startswith('>>>>>>>') and in_conflict:
                markers.append({
                    'start': conflict_start,
                    'end': i,
                    'file': filepath
                })
                in_conflict = False

        return markers

    def generate_merj_json(self) -> Dict:
        """Generate JSON format expected by merj tool."""
        # Get current status
        success, status, _ = self.run_git("git status --porcelain")

        conflicted_files = []
        if success:
            for line in status.split('\n'):
                if line.startswith('UU '):  # Both modified (conflict)
                    conflicted_files.append(line[3:])

        # Generate line numbers for conflicts
        lbd = []  # local vs base diff
        rbd = []  # remote vs base diff

        for filepath in conflicted_files:
            markers = self.get_conflict_markers(filepath)
            for marker in markers:
                # Approximate line ranges (simplified for demo)
                lbd.append({
                    "filefrom": filepath,
                    "lns": list(range(marker['start'], marker['start'] + 5))
                })
                rbd.append({
                    "filefrom": filepath,
                    "lns": list(range(marker['end'] - 5, marker['end']))
                })

        return {
            "lbd": lbd,
            "rbd": rbd,
            "conflicts": conflicted_files,
            "test_repo": str(self.test_repo_path)
        }

    def test_merj_pull(self) -> bool:
        """Test the merj pull command on the simulated conflicts."""
        print("\n🔧 Testing merj pull command...")

        # First, let's check the current state
        success, status, _ = self.run_git("git status")
        print("\nCurrent git status before pull:")
        print(status[:300] if status else "No status output")

        # Check if we have uncommitted changes that need to be handled
        if "Changes not staged" in status or "Changes to be committed" in status:
            print("⚠️  Uncommitted changes detected, committing them first...")
            self.run_git("git add .")
            self.run_git('git commit -m "Local changes before pull"')

        # Debug: check the branch status
        success, log_output, _ = self.run_git("git log --oneline -5")
        print("\n📝 Recent commits:")
        print(log_output[:300] if log_output else "No log output")

        success, fetch_output, stderr = self.run_git("git fetch")
        print("\n📥 Fetch output:", fetch_output[:200] if fetch_output else "Already up to date")
        if stderr:
            print("Fetch stderr:", stderr[:200])

        # Check remote status
        success, remote_log, _ = self.run_git("git log origin/main --oneline -5")
        print("\n📝 Remote commits:")
        print(remote_log[:300] if remote_log else "No remote commits")

        # Now run merj pull
        print("\n📥 Running 'merj pull'...")

        try:
            # Set environment to avoid editor opening
            env = os.environ.copy()
            env['GIT_EDITOR'] = 'true'  # Use 'true' command as no-op editor
            env['EDITOR'] = 'true'

            # Note: This assumes merj is installed and available
            result = subprocess.run(
                "merj pull",
                shell=True,
                cwd=self.test_repo_path,
                capture_output=True,
                text=True,
                timeout=10,  # Reduced timeout
                env=env
            )

            # Check the result
            if "Merge conflicts detected" in result.stdout or result.returncode == 2:
                print("✅ merj pull detected conflicts (as expected)")
                print("\nOutput:", result.stdout[:500] if result.stdout else "No output")

                # Check if conflicts were actually created
                success, status, _ = self.run_git("git status")
                if "both modified" in status or "Unmerged paths" in status:
                    print("✅ Conflicts successfully created by pull")
                    return True
                else:
                    print("⚠️  No conflicts detected after pull")
                    return False

            elif result.returncode == 0:
                print("✅ merj pull completed without conflicts")
                return True
            else:
                print(f"❌ merj pull failed with code {result.returncode}")
                print("\nError:", result.stderr[:500] if result.stderr else "No error output")
                return False

        except subprocess.TimeoutExpired:
            print("❌ merj pull timed out")
            return False
        except FileNotFoundError:
            print("⚠️  merj command not found. Make sure it's installed and in PATH")
            return False
        except Exception as e:
            print(f"❌ Error running merj pull: {e}")
            return False


def test_rag_pipeline_integration(conflict_json: Dict) -> bool:
    """Test the RAG pipeline with conflict data."""
    from rag_pipeline.local_remote_rag import process_git_diff_json

    print("\n🔬 Testing RAG pipeline integration...")

    try:
        # Process through RAG pipeline
        result = process_git_diff_json(
            conflict_json,
            collection_name="test_conflicts",
            k=5,
            distance_threshold=0.7,
            save_to_file=True,
            output_dir="./test_rag_output",
            verbose=False
        )

        print(f"✅ RAG pipeline processed successfully")
        print(f"  - Local chunks: {len(result.get('local_chunks', []))}")
        print(f"  - Remote chunks: {len(result.get('remote_chunks', []))}")

        # Check if output files were created
        output_dir = "./test_rag_output"
        if os.path.exists(output_dir):
            files = os.listdir(output_dir)
            print(f"  - Generated files: {files}")

            # Check LLM context file
            llm_file = os.path.join(output_dir, "llm_context.txt")
            if os.path.exists(llm_file):
                size = os.path.getsize(llm_file)
                print(f"  - LLM context file size: {size:,} bytes")

        return True

    except Exception as e:
        print(f"❌ RAG pipeline error: {e}")
        return False


def run_full_test_pipeline():
    """Run the complete test pipeline."""
    print("=" * 60)
    print("🚀 MERGE CONFLICT TEST PIPELINE")
    print("=" * 60)
    print()
    print("This pipeline will:")
    print("1. Create a temporary git repository")
    print("2. Simulate various merge conflicts")
    print("3. Test the merj pull command")
    print("4. Validate RAG pipeline processing")
    print("5. Clean up temporary files")
    print()

    results = {
        'conflicts_created': 0,
        'merj_tested': False,
        'rag_tested': False,
        'errors': []
    }

    # Use context manager for automatic cleanup
    with MergeConflictSimulator() as simulator:
        try:
            # Set up remote repository and clone it locally
            print("=" * 60)
            print("🔧 Setting Up Remote Repository")
            print("=" * 60)

            remote_path, local_path = simulator.setup_remote_and_clone()
            print(f"\n📍 Working in local repo: {local_path}")
            print(f"📡 Remote repo at: {remote_path}")
            print()

            # Create divergent changes that will cause conflicts on pull
            print("=" * 60)
            print("📝 Creating Divergent Changes")
            print("=" * 60)

            if simulator.simulate_divergent_changes():
                results['conflicts_created'] = 1
                print("✅ Successfully set up divergent changes between local and remote")

            # Test merj pull (this will create conflicts)
            print()
            print("=" * 60)
            print("🔨 Testing merj pull")
            print("=" * 60)

            results['merj_tested'] = simulator.test_merj_pull()

            # Generate merj format JSON after conflicts are created
            print()
            print("=" * 60)
            print("📋 Generating merj JSON format")
            print("=" * 60)

            merj_json = simulator.generate_merj_json()
            print(f"Conflicted files: {merj_json.get('conflicts', [])}")

            # Save JSON for reference
            json_path = local_path / "conflict_data.json"
            with open(json_path, 'w') as f:
                json.dump(merj_json, f, indent=2)
            print(f"💾 Saved conflict data to: {json_path}")

            # Test RAG pipeline with the conflicts
            print()
            print("=" * 60)
            print("🧠 Testing RAG Pipeline")
            print("=" * 60)

            results['rag_tested'] = test_rag_pipeline_integration(merj_json)

        except Exception as e:
            print(f"\n❌ Error during testing: {e}")
            results['errors'].append(str(e))

    # Print summary
    print()
    print("=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print()
    print(f"✓ Conflicts created: {results['conflicts_created']}")
    print(f"{'✓' if results['merj_tested'] else '✗'} merj pull tested: {results['merj_tested']}")
    print(f"{'✓' if results['rag_tested'] else '✗'} RAG pipeline tested: {results['rag_tested']}")

    if results['errors']:
        print(f"\n⚠️  Errors encountered: {len(results['errors'])}")
        for err in results['errors']:
            print(f"  - {err}")

    success = (results['conflicts_created'] > 0 and
              results['rag_tested'] and
              len(results['errors']) == 0)

    print()
    if success:
        print("✨ All tests completed successfully!")
    else:
        print("⚠️  Some tests did not complete successfully")

    print("=" * 60)

    return success


def test_merj_pull_with_remote():
    """Test merj pull with a proper remote repository setup."""
    print("\n🎯 Testing merj pull with remote repository")
    print("=" * 60)

    with MergeConflictSimulator() as simulator:
        # Set up remote and clone
        remote_path, local_path = simulator.setup_remote_and_clone()
        print(f"📍 Local: {local_path}")
        print(f"📡 Remote: {remote_path}")

        # Create divergent changes
        if not simulator.simulate_divergent_changes():
            print("❌ Failed to create divergent changes")
            return False

        # Test merj pull
        success = simulator.test_merj_pull()

        if success:
            # Check if conflicts were created
            _, status, _ = simulator.run_git("git status")
            if "both modified" in status or "Unmerged paths" in status:
                print("\n✅ Successfully tested merj pull with remote!")
                print("Conflicts were created as expected from pulling divergent changes.")
            else:
                print("\n✅ merj pull succeeded without conflicts")
        else:
            print("\n❌ merj pull test failed")

        return success


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test merge conflict pipeline")
    parser.add_argument("--quick", action="store_true",
                      help="Run quick test with remote repository")
    parser.add_argument("--full", action="store_true",
                      help="Run full test pipeline")

    args = parser.parse_args()

    if args.quick:
        # Quick test with remote setup
        success = test_merj_pull_with_remote()
    elif args.full:
        # Full test pipeline
        success = run_full_test_pipeline()
    else:
        # Default to quick test
        success = test_merj_pull_with_remote()

    sys.exit(0 if success else 1)