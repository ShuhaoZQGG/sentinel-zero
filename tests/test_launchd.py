"""Tests for macOS launchd integration"""

import os
import sys
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess


class TestLaunchdIntegration:
    """Test launchd service integration"""
    
    def test_plist_file_structure(self):
        """Test that plist file has correct structure"""
        plist_path = Path(__file__).parent.parent / "launchd" / "com.sentinelzero.plist"
        assert plist_path.exists(), "Plist file should exist"
        
        # Read and validate plist content
        import plistlib
        with open(plist_path, 'rb') as f:
            plist = plistlib.load(f)
        
        # Check required keys
        assert plist['Label'] == 'com.sentinelzero'
        assert 'ProgramArguments' in plist
        assert plist['RunAtLoad'] is True
        assert 'KeepAlive' in plist
        assert 'StandardOutPath' in plist
        assert 'StandardErrorPath' in plist
    
    @pytest.mark.skipif(sys.platform != "darwin", reason="macOS only test")
    def test_install_script_exists(self):
        """Test that install script exists and is executable"""
        install_script = Path(__file__).parent.parent / "launchd" / "install.sh"
        assert install_script.exists(), "Install script should exist"
        
        # Check script has shebang
        with open(install_script, 'r') as f:
            first_line = f.readline()
            assert first_line.startswith('#!/bin/bash'), "Script should have bash shebang"
    
    @pytest.mark.skipif(sys.platform != "darwin", reason="macOS only test")
    def test_uninstall_script_exists(self):
        """Test that uninstall script exists"""
        uninstall_script = Path(__file__).parent.parent / "launchd" / "uninstall.sh"
        assert uninstall_script.exists(), "Uninstall script should exist"
        
        # Check script has shebang
        with open(uninstall_script, 'r') as f:
            first_line = f.readline()
            assert first_line.startswith('#!/bin/bash'), "Script should have bash shebang"
    
    @patch('subprocess.run')
    def test_daemon_command_starts_service(self, mock_run):
        """Test that daemon command starts the API service"""
        from src.cli.main import cli
        from click.testing import CliRunner
        
        runner = CliRunner()
        
        # Mock both uvicorn and scheduler to prevent actual service start
        with patch('src.cli.main.uvicorn') as mock_uvicorn:
            with patch('src.cli.main.scheduler.start') as mock_scheduler:
                result = runner.invoke(cli, ['daemon'])
                
                # Check scheduler was started
                mock_scheduler.assert_called_once()
                
                # Check uvicorn was called with correct parameters
                mock_uvicorn.run.assert_called_once()
                call_args = mock_uvicorn.run.call_args
                assert call_args[1]['port'] == 8000
                assert call_args[1]['host'] == '0.0.0.0'
    
    @pytest.mark.skipif(sys.platform != "darwin", reason="macOS only test")
    def test_launchctl_command_format(self):
        """Test launchctl command format in scripts"""
        install_script = Path(__file__).parent.parent / "launchd" / "install.sh"
        
        with open(install_script, 'r') as f:
            content = f.read()
        
        # Check for correct launchctl commands
        assert 'launchctl load' in content
        assert 'launchctl unload' in content
        assert 'launchctl list' in content
    
    def test_service_paths_configuration(self):
        """Test that service paths are correctly configured"""
        plist_path = Path(__file__).parent.parent / "launchd" / "com.sentinelzero.plist"
        
        import plistlib
        with open(plist_path, 'rb') as f:
            plist = plistlib.load(f)
        
        # Check paths
        assert plist['StandardOutPath'] == '/usr/local/var/log/sentinelzero.log'
        assert plist['StandardErrorPath'] == '/usr/local/var/log/sentinelzero.error.log'
        assert plist['WorkingDirectory'] == '/usr/local/var/sentinelzero'
        
        # Check environment variables
        assert 'EnvironmentVariables' in plist
        assert 'PATH' in plist['EnvironmentVariables']
        assert 'SENTINELZERO_HOME' in plist['EnvironmentVariables']
    
    def test_keepalive_configuration(self):
        """Test KeepAlive settings for auto-restart"""
        plist_path = Path(__file__).parent.parent / "launchd" / "com.sentinelzero.plist"
        
        import plistlib
        with open(plist_path, 'rb') as f:
            plist = plistlib.load(f)
        
        # Check KeepAlive configuration
        keepalive = plist['KeepAlive']
        assert keepalive['SuccessfulExit'] is False  # Don't restart on successful exit
        assert keepalive['Crashed'] is True  # Restart on crash
    
    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_install_creates_directories(self, mock_run, mock_exists):
        """Test that install script creates required directories"""
        # This would require actually running the script or parsing it
        # For now, we just verify the script contains mkdir commands
        install_script = Path(__file__).parent.parent / "launchd" / "install.sh"
        
        with open(install_script, 'r') as f:
            content = f.read()
        
        # Check for directory creation commands
        assert 'mkdir -p' in content
        assert '/usr/local/var/log' in content
        assert '/usr/local/var/sentinelzero' in content
        assert '/usr/local/bin' in content