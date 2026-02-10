#!/bin/bash
# betamax/lib/entropy_detector.sh - Roadmap entropy detection and analysis

# Extract documented features from README.md
extract_readme_features() {
  local readme_file="${1:-.}/README.md"
  [[ ! -f "$readme_file" ]] && return

  # Features mentioned in README headers, feature lists, and options tables
  grep -E "^##|^\|.*\|" "$readme_file" | \
    grep -v "^##.*License" | \
    sed 's/|//g' | \
    grep -v "^$" | \
    sort -u
}

# Extract @set directives from .keys files to identify feature usage
extract_keys_features() {
  local dir="${1:-.}"
  find "$dir" -name "*.keys" -type f -exec grep -h "^@" {} \; | \
    sed 's/@//' | \
    cut -d: -f1 | \
    sort -u
}

# Extract implemented shell functions
extract_shell_functions() {
  local dir="${1:-.}/lib"
  [[ ! -d "$dir" ]] && return

  find "$dir" -name "*.sh" -type f -exec grep -h "^[a-z_][a-z0-9_]*() {" {} \; | \
    sed 's/() {//' | \
    sort -u
}

# Extract Python functions and classes
extract_python_functions() {
  local dir="${1:-.}/lib/python"
  [[ ! -d "$dir" ]] && return

  find "$dir" -name "*.py" -type f | while read -r file; do
    grep -h "^def \|^class " "$file" | \
      sed 's/def //;s/class //' | \
      sed 's/(.*//g' | \
      sort -u
  done
}

# Extract bin scripts
extract_bin_scripts() {
  local dir="${1:-.}/bin"
  [[ ! -d "$dir" ]] && return

  ls -1 "$dir" 2>/dev/null | grep -v "^\..*"
}

# Analyze git commit patterns for feature vs bugfix vs refactor
analyze_git_patterns() {
  local repo_dir="${1:-.}"
  cd "$repo_dir" || return

  # Last 50 commits
  git log --oneline -50 2>/dev/null | while read -r hash msg; do
    if [[ "$msg" =~ ^feat: ]]; then
      echo "feature|$msg"
    elif [[ "$msg" =~ ^fix: ]]; then
      echo "bugfix|$msg"
    elif [[ "$msg" =~ ^refactor: ]]; then
      echo "refactor|$msg"
    elif [[ "$msg" =~ ^docs: ]]; then
      echo "documentation|$msg"
    else
      echo "other|$msg"
    fi
  done
}

# Check for orphaned code (functions defined but never called)
detect_orphaned_code() {
  local dir="${1:-.}/lib"
  [[ ! -d "$dir" ]] && return

  find "$dir" -name "*.sh" -type f | while read -r file; do
    grep -h "^[a-z_][a-z0-9_]*() {" "$file" | sed 's/() {//' | while read -r func; do
      # Count calls to this function (excluding definition)
      count=$(grep -r "$func" "$dir" --include="*.sh" | grep -vc "^[^:]*:$func() {" 2>/dev/null || echo "0")
      count=$(echo "$count" | tr -d ' ')
      if [[ "$count" == "0" ]]; then
        echo "orphaned|${file##*/}|$func"
      fi
    done
  done
}

# Compute entropy score based on discrepancies
compute_entropy_score() {
  local total_checks=0
  local issues=0

  # Check 1: Documented vs implemented features
  local readme_features=$(extract_readme_features "$1" | wc -l)
  local implemented=$(extract_shell_functions "$1" 2>/dev/null | wc -l)
  ((total_checks++))

  if [[ $readme_features -gt $((implemented * 2)) ]]; then
    ((issues++))
  fi

  # Check 2: Keys files without matching implementation
  local keys_count=$(find "$1" -name "*.keys" -type f 2>/dev/null | wc -l)
  ((total_checks++))
  if [[ $keys_count -gt 5 ]]; then
    ((issues++))
  fi

  # Check 3: Orphaned code
  local orphaned=$(detect_orphaned_code "$1" | wc -l)
  ((total_checks++))
  if [[ $orphaned -gt 0 ]]; then
    ((issues++))
  fi

  # Check 4: Git commit consistency
  local git_patterns=$(analyze_git_patterns "$1" | cut -d'|' -f1 | sort | uniq -c | sort -rn)
  local feat_count=$(echo "$git_patterns" | grep feature | awk '{print $1}')
  feat_count=${feat_count:-0}
  local bug_count=$(echo "$git_patterns" | grep bugfix | awk '{print $1}')
  bug_count=${bug_count:-0}
  ((total_checks++))

  # If features >> bugs, suggests incomplete feature implementation
  if [[ $feat_count -gt $((bug_count * 3)) ]]; then
    ((issues++))
  fi

  # Calculate entropy as percentage of issues
  local entropy=$((issues * 100 / total_checks))
  echo "$entropy"
}

# Generate detailed entropy report
generate_entropy_report() {
  local repo_dir="${1:-.}"
  local entropy_score=$(compute_entropy_score "$repo_dir")

  cat << EOF
{
  "entropy_score": $entropy_score,
  "status": "$(
    if [[ $entropy_score -lt 20 ]]; then
      echo "healthy"
    elif [[ $entropy_score -lt 50 ]]; then
      echo "warning"
    else
      echo "critical"
    fi
  )",
  "analysis": {
    "orphaned_code": $(detect_orphaned_code "$repo_dir" | wc -l),
    "git_commits": {
      "features": $(analyze_git_patterns "$repo_dir" | grep -c "^feature|"),
      "bugfixes": $(analyze_git_patterns "$repo_dir" | grep -c "^bugfix|"),
      "refactors": $(analyze_git_patterns "$repo_dir" | grep -c "^refactor|")
    },
    "documented_features": $(extract_readme_features "$repo_dir" | wc -l),
    "implemented_functions": $(extract_shell_functions "$repo_dir" 2>/dev/null | wc -l),
    "python_functions": $(extract_python_functions "$repo_dir" 2>/dev/null | wc -l),
    "bin_scripts": $(extract_bin_scripts "$repo_dir" | wc -l)
  }
}
EOF
}

# Detect unimplemented features (mentioned in README but no code)
detect_unimplemented_features() {
  local repo_dir="${1:-.}"
  local unimplemented=()

  # Common feature indicators in README
  local features=("record" "capture" "GIF" "screenshot" "PNG" "HTML" "decoration" "theme")

  for feature in "${features[@]}"; do
    if grep -q "$feature" "$repo_dir/README.md" 2>/dev/null; then
      # Check if implemented
      if ! grep -r "$feature" "$repo_dir/lib" "$repo_dir/bin" --include="*.sh" --include="*.py" 2>/dev/null | grep -q "$(echo "$feature" | tr '[:upper:]' '[:lower:]')"; then
        unimplemented+=("$feature")
      fi
    fi
  done

  printf '%s\n' "${unimplemented[@]}"
}

# Detect scope creep (code that exists but isn't documented)
detect_scope_creep() {
  local repo_dir="${1:-.}"
  local undocumented=()

  # Find functions/scripts not mentioned in README
  extract_shell_functions "$repo_dir" | while read -r func; do
    if ! grep -q "$func" "$repo_dir/README.md" 2>/dev/null; then
      echo "undocumented_function|$func"
    fi
  done

  extract_bin_scripts "$repo_dir" | while read -r script; do
    if ! grep -q "$script" "$repo_dir/README.md" 2>/dev/null && [[ "$script" != "betamax-"* ]]; then
      echo "undocumented_script|$script"
    fi
  done
}
