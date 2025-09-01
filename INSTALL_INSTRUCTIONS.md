# SentinelZero Installation Instructions

## Quick Installation

The `sentinel-zero` command is now available! Here are your options to use it:

### Option 1: Use from Project Directory
```bash
cd /Users/shuhaozhang/Project/sentinel-zero
./sentinel-zero --version
```

### Option 2: Add to PATH (Recommended)
Add this line to your `~/.zshrc` or `~/.bash_profile`:
```bash
export PATH="/Users/shuhaozhang/Project/sentinel-zero:$PATH"
```

Then reload your shell:
```bash
source ~/.zshrc  # or source ~/.bash_profile
```

Now you can use `sentinel-zero` from anywhere:
```bash
sentinel-zero --version
```

### Option 3: Create System-wide Link (Requires sudo)
```bash
sudo ln -sf /Users/shuhaozhang/Project/sentinel-zero/sentinel-zero /usr/local/bin/sentinel-zero
```

## What Was Fixed

1. **setup.py**: Fixed the entry point from `sentinel=cli.main:cli` to `sentinel-zero=src.cli.main:cli`
2. **Package structure**: Corrected the package discovery configuration
3. **Created wrapper script**: Made a shell script that activates the virtual environment automatically
4. **Virtual environment**: The package is installed in `.venv` to avoid system Python conflicts

## Testing the Installation

Run these commands to verify everything works:

```bash
# Check version
./sentinel-zero --version

# Get help
./sentinel-zero --help

# Start a test process
./sentinel-zero start --name "test" --cmd "echo 'Hello, SentinelZero!'"

# Check status
./sentinel-zero status

# List processes
./sentinel-zero list
```

## Troubleshooting

If you get "command not found" errors:
1. Make sure you're in the project directory: `/Users/shuhaozhang/Project/sentinel-zero`
2. Use the wrapper script: `./sentinel-zero` (with the `./` prefix)
3. Or add the directory to your PATH as shown above

## For Development

If you need to modify the code:
```bash
# Activate the virtual environment
source .venv/bin/activate

# Now you can use sentinel-zero directly
sentinel-zero --version

# To deactivate when done
deactivate
```