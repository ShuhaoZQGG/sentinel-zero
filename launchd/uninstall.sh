#!/bin/bash

# SentinelZero launchd uninstallation script

set -e

PLIST_NAME="com.sentinelzero.plist"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME"
INSTALL_DIR="/usr/local/bin"

echo "SentinelZero launchd Uninstallation Script"
echo "==========================================="

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "Error: This script is for macOS only"
    exit 1
fi

# Unload the launch agent
if [ -f "$PLIST_PATH" ]; then
    echo "Unloading launch agent..."
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    
    echo "Removing plist file..."
    rm -f "$PLIST_PATH"
else
    echo "Launch agent not found at $PLIST_PATH"
fi

# Remove command wrapper
if [ -f "$INSTALL_DIR/sentinelzero" ]; then
    echo "Removing command wrapper..."
    sudo rm -f "$INSTALL_DIR/sentinelzero"
fi

# Verify uninstallation
if ! launchctl list | grep -q "com.sentinelzero"; then
    echo ""
    echo "✅ SentinelZero has been successfully uninstalled!"
    echo ""
    echo "Note: Log files and working directory have been preserved at:"
    echo "  - /usr/local/var/log/sentinelzero*"
    echo "  - /usr/local/var/sentinelzero/"
    echo ""
    echo "To remove these as well, run:"
    echo "  sudo rm -rf /usr/local/var/log/sentinelzero*"
    echo "  sudo rm -rf /usr/local/var/sentinelzero"
else
    echo ""
    echo "⚠️  Warning: Service may still be running"
    echo "Try running: launchctl remove com.sentinelzero"
fi