#!/usr/bin/env python3
"""
Entropy analyzer for roadmap drift detection.

Analyzes documented features in README and configuration against actual
implementation in code, git history, and structure to detect scope creep.
"""

import json
import os
import re
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional


@dataclass
class EntropyStat:
    """Entropy analysis statistics."""
    entropy_score: int
    status: str
    documented_features: int
    implemented_functions: int
    python_functions: int
    bin_scripts: int
    orphaned_code: int
    unimplemented_features: List[str]
    scope_creep: List[Tuple[str, str]]
    git_analysis: Dict[str, int]


class EntropyAnalyzer:
    """Analyzes codebase for scope creep and drift."""

    def __init__(self, repo_dir: str = "."):
        """Initialize analyzer for a repository directory."""
        self.repo_dir = Path(repo_dir).resolve()
        self.lib_dir = self.repo_dir / "lib"
        self.bin_dir = self.repo_dir / "bin"
        self.readme = self.repo_dir / "README.md"

    def extract_readme_features(self) -> Set[str]:
        """Extract documented features from README.md."""
        if not self.readme.exists():
            return set()

        features = set()
        with open(self.readme) as f:
            content = f.read()
            # Extract section headers
            headers = re.findall(r"^## (.+?)$", content, re.MULTILINE)
            features.update(h.lower() for h in headers)
            # Extract options from tables
            options = re.findall(r"\|\s+(\w+(?:-\w+)*)\s+\|", content)
            features.update(o.lower() for o in options)
        return features

    def extract_shell_functions(self) -> Set[str]:
        """Extract function definitions from shell scripts."""
        functions = set()
        if not self.lib_dir.exists():
            return functions

        for sh_file in self.lib_dir.glob("*.sh"):
            with open(sh_file) as f:
                pattern = re.compile(r"^([a-z_][a-z0-9_]*)\(\) \{", re.MULTILINE)
                functions.update(pattern.findall(f.read()))
        return functions

    def extract_python_functions(self) -> Set[str]:
        """Extract function and class definitions from Python."""
        functions = set()
        python_dir = self.lib_dir / "python"
        if not python_dir.exists():
            return functions

        for py_file in python_dir.glob("*.py"):
            with open(py_file) as f:
                pattern = re.compile(r"^(?:def|class) ([a-z_][a-z0-9_]*)", re.MULTILINE)
                functions.update(pattern.findall(f.read()))
        return functions

    def extract_bin_scripts(self) -> Set[str]:
        """Extract available bin scripts."""
        scripts = set()
        if not self.bin_dir.exists():
            return scripts

        for item in self.bin_dir.iterdir():
            if item.is_file() and os.access(item, os.X_OK):
                scripts.add(item.name)
        return scripts

    def detect_orphaned_code(self) -> List[Tuple[str, str]]:
        """Find functions defined but never called."""
        orphaned = []
        if not self.lib_dir.exists():
            return orphaned

        # Get all defined functions
        all_functions = self.extract_shell_functions()

        # Check each function for calls
        for func in all_functions:
            call_count = 0
            for sh_file in self.lib_dir.glob("*.sh"):
                with open(sh_file) as f:
                    content = f.read()
                    # Count calls (excluding definition)
                    pattern = f"({func}|call {func})"
                    matches = len(re.findall(pattern, content))
                    # Subtract definition itself
                    definition = re.search(rf"^{func}\(\) \{{", content, re.MULTILINE)
                    if definition:
                        matches -= 1
                    call_count += matches

            if call_count == 0:
                orphaned.append(("function", func))
        return orphaned

    def analyze_git_patterns(self) -> Dict[str, int]:
        """Analyze git commit patterns."""
        patterns = {"feature": 0, "bugfix": 0, "refactor": 0, "documentation": 0, "other": 0}

        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-50"],
                cwd=self.repo_dir,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                return patterns

            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                msg = line.split(" ", 1)[1] if " " in line else ""
                if msg.startswith("feat:"):
                    patterns["feature"] += 1
                elif msg.startswith("fix:"):
                    patterns["bugfix"] += 1
                elif msg.startswith("refactor:"):
                    patterns["refactor"] += 1
                elif msg.startswith("docs:"):
                    patterns["documentation"] += 1
                else:
                    patterns["other"] += 1
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return patterns

    def detect_unimplemented_features(self) -> List[str]:
        """Find features documented but not implemented."""
        unimplemented = []
        readme_features = self.extract_readme_features()
        shell_funcs = self.extract_shell_functions()
        python_funcs = self.extract_python_functions()
        all_implementations = shell_funcs | python_funcs

        for feature in readme_features:
            # Check if feature is mentioned in implementation
            found = False
            for impl in all_implementations:
                if feature.replace("-", "_") in impl.lower() or impl.lower() in feature:
                    found = True
                    break
            if not found:
                unimplemented.append(feature)

        return unimplemented

    def detect_scope_creep(self) -> List[Tuple[str, str]]:
        """Find code that exists but isn't documented."""
        creep = []
        readme_content = self.readme.read_text() if self.readme.exists() else ""

        # Check undocumented functions
        for func in self.extract_shell_functions():
            if func not in readme_content:
                creep.append(("function", func))

        # Check undocumented scripts
        for script in self.extract_bin_scripts():
            if script.startswith("betamax-"):
                subcommand = script.replace("betamax-", "")
                if subcommand not in readme_content:
                    creep.append(("subcommand", subcommand))

        return creep

    def compute_entropy_score(self) -> int:
        """Compute entropy score (0-100)."""
        issues = 0
        total_checks = 4

        # Check 1: Feature gap
        readme_count = len(self.extract_readme_features())
        impl_count = len(self.extract_shell_functions())
        if readme_count > impl_count * 2:
            issues += 1

        # Check 2: Orphaned code
        if self.detect_orphaned_code():
            issues += 1

        # Check 3: Scope creep
        if self.detect_scope_creep():
            issues += 1

        # Check 4: Feature-heavy commits
        patterns = self.analyze_git_patterns()
        if patterns["feature"] > patterns["bugfix"] * 3:
            issues += 1

        return int((issues / total_checks) * 100)

    def analyze(self) -> EntropyStat:
        """Run full entropy analysis."""
        entropy_score = self.compute_entropy_score()
        status = "healthy" if entropy_score < 20 else "warning" if entropy_score < 50 else "critical"

        return EntropyStat(
            entropy_score=entropy_score,
            status=status,
            documented_features=len(self.extract_readme_features()),
            implemented_functions=len(self.extract_shell_functions()),
            python_functions=len(self.extract_python_functions()),
            bin_scripts=len(self.extract_bin_scripts()),
            orphaned_code=len(self.detect_orphaned_code()),
            unimplemented_features=self.detect_unimplemented_features(),
            scope_creep=self.detect_scope_creep(),
            git_analysis=self.analyze_git_patterns(),
        )


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Analyze roadmap entropy and scope creep")
    parser.add_argument("repo", nargs="?", default=".", help="Repository directory")
    parser.add_argument("-j", "--json", action="store_true", help="Output as JSON")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    analyzer = EntropyAnalyzer(args.repo)
    result = analyzer.analyze()

    if args.json:
        print(json.dumps(asdict(result), indent=2))
    else:
        print(f"Entropy Score: {result.entropy_score}/100 ({result.status})")
        if args.verbose:
            print(f"Documented Features: {result.documented_features}")
            print(f"Implemented Functions: {result.implemented_functions}")
            print(f"Orphaned Code: {result.orphaned_code}")
            print(f"Git Patterns: {result.git_analysis}")


if __name__ == "__main__":
    main()
