#!/usr/bin/env bash
# install-hooks.sh — instaluje Git hooks z .github/hooks/ do .git/hooks/
# Uruchom z katalogu głównego repozytorium:
#   bash .github/hooks/install-hooks.sh

set -e

REPO_ROOT=$(git rev-parse --show-toplevel)
HOOKS_DIR="$REPO_ROOT/.git/hooks"
SOURCE_DIR="$REPO_ROOT/.github/hooks"

echo "Instalowanie Git hooks..."
echo "  Źródło: $SOURCE_DIR"
echo "  Cel   : $HOOKS_DIR"
echo ""

# post-commit
cat > "$HOOKS_DIR/post-commit" << 'EOF'
#!/bin/sh
# auto-generated post-commit hook
if command -v pwsh >/dev/null 2>&1; then
    pwsh -NoProfile -ExecutionPolicy Bypass -File "$(git rev-parse --show-toplevel)/.github/hooks/post-commit.ps1"
elif command -v powershell >/dev/null 2>&1; then
    powershell -NoProfile -ExecutionPolicy Bypass -File "$(git rev-parse --show-toplevel)/.github/hooks/post-commit.ps1"
else
    "$(git rev-parse --show-toplevel)/.github/hooks/post-commit"
fi
EOF
chmod +x "$HOOKS_DIR/post-commit"
echo "  ✅ post-commit"

# pre-commit (guard-git)
cat > "$HOOKS_DIR/pre-commit" << 'EOF'
#!/bin/sh
# auto-generated pre-commit hook (guard-git)
if command -v pwsh >/dev/null 2>&1; then
    pwsh -NoProfile -ExecutionPolicy Bypass -File "$(git rev-parse --show-toplevel)/.github/hooks/scripts/guard-git.ps1" -HookType pre-commit
elif command -v powershell >/dev/null 2>&1; then
    powershell -NoProfile -ExecutionPolicy Bypass -File "$(git rev-parse --show-toplevel)/.github/hooks/scripts/guard-git.ps1" -HookType pre-commit
fi
EOF
chmod +x "$HOOKS_DIR/pre-commit"
echo "  ✅ pre-commit"

# pre-push (guard-git)
cat > "$HOOKS_DIR/pre-push" << 'EOF'
#!/bin/sh
# auto-generated pre-push hook (guard-git)
if command -v pwsh >/dev/null 2>&1; then
    pwsh -NoProfile -ExecutionPolicy Bypass -File "$(git rev-parse --show-toplevel)/.github/hooks/scripts/guard-git.ps1" -HookType pre-push "$1" "$2"
elif command -v powershell >/dev/null 2>&1; then
    powershell -NoProfile -ExecutionPolicy Bypass -File "$(git rev-parse --show-toplevel)/.github/hooks/scripts/guard-git.ps1" -HookType pre-push "$1" "$2"
fi
EOF
chmod +x "$HOOKS_DIR/pre-push"
echo "  ✅ pre-push"

echo ""
echo "Gotowe! Hooks zainstalowane w: $HOOKS_DIR"
