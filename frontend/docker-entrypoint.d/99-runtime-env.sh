#!/bin/sh
set -eu

ENV_JS_PATH="/usr/share/nginx/html/env.js"

escape_js() {
  # Escape backslashes and double quotes for safe JS string literals
  printf '%s' "${1-}" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'
}

VITE_API_URL_VALUE="${VITE_API_URL-}"
VITE_API_KEY_VALUE="${VITE_API_KEY-}"

cat > "$ENV_JS_PATH" <<EOF
window.__FW_ENV = {
  VITE_API_URL: "$(escape_js "$VITE_API_URL_VALUE")",
  VITE_API_KEY: "$(escape_js "$VITE_API_KEY_VALUE")",
};
EOF

# Make sure file is readable
chmod 644 "$ENV_JS_PATH" || true
