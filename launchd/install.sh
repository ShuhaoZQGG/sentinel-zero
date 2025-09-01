#!/bin/bash

# SentinelZero launchd installation script

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PLIST_NAME="com.sentinelzero.plist"
PLIST_SOURCE="$SCRIPT_DIR/$PLIST_NAME"
PLIST_DEST="$HOME/Library/LaunchAgents/$PLIST_NAME"
INSTALL_DIR="/usr/local/bin"
LOG_DIR="/usr/local/var/log"
WORK_DIR="/usr/local/var/sentinelzero"

echo "SentinelZero launchd Installation Script"
echo "========================================"

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "Error: This script is for macOS only"
    exit 1
fi

# Create required directories
echo "Creating directories..."
sudo mkdir -p "$LOG_DIR"
sudo mkdir -p "$WORK_DIR"
sudo mkdir -p "$INSTALL_DIR"

# Install Python package
echo "Installing SentinelZero package..."
cd "$PROJECT_ROOT"
pip install -e .

# Create sentinelzero command wrapper
echo "Creating command wrapper..."
cat > /tmp/sentinelzero << 'EOF'
#!/bin/bash
source "$HOME/.zshrc" 2>/dev/null || source "$HOME/.bash_profile" 2>/dev/null
python -m src.cli.main "$@"
EOF

sudo mv /tmp/sentinelzero "$INSTALL_DIR/sentinelzero"
sudo chmod +x "$INSTALL_DIR/sentinelzero"

# Copy plist file
echo "Installing launchd configuration..."
cp "$PLIST_SOURCE" "$PLIST_DEST"

# Load the launch agent
echo "Loading launch agent..."
launchctl unload "$PLIST_DEST" 2>/dev/null || true
launchctl load "$PLIST_DEST"

# Verify installation
if launchctl list | grep -q "com.sentinelzero"; then
    echo ""
    echo "✅ SentinelZero has been successfully installed as a launchd service!"
    echo ""
    echo "Service status:"
    launchctl list | grep "com.sentinelzero"
    echo ""
    echo "Logs location:"
    echo "  - Standard output: $LOG_DIR/sentinelzero.log"
    echo "  - Error output: $LOG_DIR/sentinelzero.error.log"
    echo ""
    echo "To manage the service:"
    echo "  - Stop: launchctl unload $PLIST_DEST"
    echo "  - Start: launchctl load $PLIST_DEST"
    echo "  - Status: launchctl list | grep com.sentinelzero"
else
    echo ""
    echo "⚠️  Warning: Service may not have started correctly"
    echo "Check logs at: $LOG_DIR/sentinelzero.error.log"
fi