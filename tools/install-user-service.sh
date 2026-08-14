#!/usr/bin/env bash
set -euo pipefail

# PERSONAL CIC 003h-A0.2 deployment configuration boundary
CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
DEPLOY_DIR="${CONFIG_HOME}/personal-cic"
DEPLOY_CONFIG="${DEPLOY_DIR}/runtime.json"
SOURCE_TEMPLATE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/config/runtime.example.json"

mkdir -p "$DEPLOY_DIR"
chmod 700 "$DEPLOY_DIR"
if [[ ! -e "$DEPLOY_CONFIG" ]]; then
    install -m 600 "$SOURCE_TEMPLATE" "$DEPLOY_CONFIG"
    echo "Initialized neutral deployment config at $DEPLOY_CONFIG"
    echo "Configure deployment/site/provider values before enabling remote awareness."
else
    chmod 600 "$DEPLOY_CONFIG"
fi


PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_DIR="${HOME}/.config/systemd/user"
SERVICE_FILE="${SERVICE_DIR}/personal-cic.service"
RUNTIME="${PROJECT_ROOT}/.venv/bin/cic-runtime"

if [[ ! -x "${RUNTIME}" ]]; then
    echo "Missing runtime executable: ${RUNTIME}" >&2
    echo "Activate the project venv and run: python -m pip install -e ." >&2
    exit 1
fi

VERIFY_SOURCE="${PROJECT_ROOT}/tools/verify-source-distribution.py"
if [[ ! -x "${VERIFY_SOURCE}" ]]; then
    echo "Missing source-distribution verifier: ${VERIFY_SOURCE}" >&2
    exit 1
fi
if ! "${PROJECT_ROOT}/.venv/bin/python" "${VERIFY_SOURCE}" --working-tree --require-runtime-vendor; then
    echo "Refusing service install: working-tree/source dependency verification failed." >&2
    exit 1
fi

mkdir -p "${SERVICE_DIR}"

cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=Personal CIC Persistent Runtime
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=${PROJECT_ROOT}
ExecStart=${RUNTIME} --config ${DEPLOY_CONFIG} --health-config config/health.json
Restart=on-failure
RestartSec=3
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=-${HOME}/.config/personal-cic/secrets.env
NoNewPrivileges=true
UMask=0077

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now personal-cic.service

echo
echo "Installed and started: ${SERVICE_FILE}"
echo "Status: systemctl --user status personal-cic.service"
echo "Logs:   journalctl --user -u personal-cic.service -f"
echo
echo "For boot-before-login behavior, enable user lingering once:"
echo "  sudo loginctl enable-linger ${USER}"
