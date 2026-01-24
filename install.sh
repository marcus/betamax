#!/bin/bash
# Idempotent installer for betamax
# Creates a symlink in ~/.local/bin and ensures it's on PATH

set -e

INSTALL_DIR="${HOME}/.local/bin"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MARKER="# Added by betamax install"

main() {
  # Create install dir
  mkdir -p "$INSTALL_DIR"

  # Symlink main executable (ln -sf is idempotent)
  ln -sf "$SCRIPT_DIR/betamax" "$INSTALL_DIR/betamax"
  echo "Linked: $INSTALL_DIR/betamax -> $SCRIPT_DIR/betamax"

  # Check if already on PATH
  if echo "$PATH" | tr ':' '\n' | grep -qx "$INSTALL_DIR"; then
    echo "betamax is on your PATH. Ready to use."
    return
  fi

  # Determine shell rc file
  local rc_file
  case "$(basename "$SHELL")" in
    zsh)  rc_file="$HOME/.zshrc" ;;
    bash)
      if [[ -f "$HOME/.bash_profile" ]]; then
        rc_file="$HOME/.bash_profile"
      else
        rc_file="$HOME/.bashrc"
      fi
      ;;
    fish) rc_file="$HOME/.config/fish/config.fish" ;;
    *)    rc_file="$HOME/.profile" ;;
  esac

  # Add to PATH if marker not already present (idempotent)
  if [[ -f "$rc_file" ]] && grep -qF "$MARKER" "$rc_file"; then
    echo "PATH entry already in $rc_file. Ready to use."
    return
  fi

  if [[ "$(basename "$SHELL")" == "fish" ]]; then
    echo "fish_add_path $INSTALL_DIR $MARKER" >> "$rc_file"
  else
    printf '\nexport PATH="%s:$PATH" %s\n' "$INSTALL_DIR" "$MARKER" >> "$rc_file"
  fi

  echo "Added $INSTALL_DIR to PATH in $rc_file"
  echo "Run: source $rc_file (or open a new terminal)"
}

main
