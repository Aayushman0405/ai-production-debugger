#!/bin/bash

echo "🔧 Installing kubectl AI debug plugin..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_PATH="/usr/local/bin/kubectl-ai-debug"

if [ -w "/usr/local/bin" ]; then
    cp "$SCRIPT_DIR/kubectl-ai-debug" "$PLUGIN_PATH"
    chmod +x "$PLUGIN_PATH"
    echo "✅ Plugin installed! Usage: kubectl ai-debug <namespace> [minutes]"
else
    echo "❌ Need sudo to install to /usr/local/bin"
    sudo cp "$SCRIPT_DIR/kubectl-ai-debug" "$PLUGIN_PATH"
    sudo chmod +x "$PLUGIN_PATH"
    echo "✅ Plugin installed! Usage: kubectl ai-debug <namespace> [minutes]"
fi
