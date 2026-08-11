#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_DIR="${HOME}/.config/systemd/user"
SERVICE_FILE="${SERVICE_DIR}/personal-cic.service"
RUNTIME="${PROJECT_ROOT}/.venv/bin/cic-runtime"

if [[ ! -x "${RUNTIME}" ]]; then
    echo "Missing runtime executable: ${RUNTIME}" >&2
    echo "Activate the project venv and run: python -m pip install -e ." >&2
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
ExecStart=${RUNTIME} --config config/runtime.json --health-config config/health.json
Restart=on-failure
RestartSec=3
Environment=PYTHONUNBUFFERED=1

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
