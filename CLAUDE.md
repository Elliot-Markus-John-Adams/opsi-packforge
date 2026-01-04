# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OPSI PackForge is a PowerShell-based installer that creates a Windows Batch application for managing OPSI packages in paedML Linux educational environments. The project consists primarily of a single PowerShell installer script that generates the entire application at runtime.

## Key Architecture

- **Single Script Architecture**: The entire application is embedded within `install.ps1` as a multi-line string
- **Self-Contained**: The installer downloads Python runtime and creates all necessary files
- **Generated Application**: The main app (`opsi_packforge.bat`) is created during installation, not stored in the repository

## Development Commands

### Testing the Installer
```powershell
# Run installer locally
.\install.ps1

# Test mode installation (option 2 during execution)
.\install.ps1
# Then select option 2 for test mode
```

### Working with the Embedded Application

The main application code is embedded in `install.ps1` starting at line ~87 as a multi-line string in the `$batchScript` variable. When modifying the application:

1. Edit the Batch script content within the `$batchScript` variable in `install.ps1`
2. Test changes by running the installer and selecting test mode
3. The generated application will be at `%LOCALAPPDATA%\OPSI-PackForge\app\opsi_packforge.bat`

## Code Structure

- **install.ps1**: Contains all logic - installer, application code, and desktop shortcut creation
  - Lines 1-86: PowerShell installer logic
  - Lines 87-656: Embedded Batch application (`$batchScript` variable)
  - Lines 657-end: Installation execution and cleanup

## Testing Approach

Manual testing workflow for OPSI package changes:
1. Create/update package locally using the application
2. Test on a single client first (`opsi-admin -d method configState_create`)
3. Monitor installation via logs: `/var/log/opsi/clientconnect/<client>.log`
4. Deploy to production after verification

## Important Considerations

- **Language**: Primary user interface is in German (target audience: German educational institutions)
- **Environment**: Assumes Windows 10/11 with PowerShell 5.1+ and access to OPSI server (default: 10.1.0.2)
- **SSH Requirements**: Requires Windows OpenSSH client and SSH access to OPSI server
- **Embedded Python**: Downloads Python 3.11.9 automatically during installation

## Common Development Tasks

### Modifying Application Features
Edit the Batch script within `$batchScript` variable in install.ps1. Key sections:
- Main menu: Around line 150-200 in the embedded script
- Package creation logic: Lines 200-350
- Server communication: Lines 400-500
- Silent installer parameters: Lines 250-300

### Adding New Installer Types
Add new silent parameters in the package creation section of the embedded Batch script (search for "NSIS", "MSI", "InnoSetup" patterns).

### Updating Python Version
Modify the download URL and extraction logic in install.ps1 (around lines 20-40).

## Git Workflow

Standard git workflow with main branch. Recent commit pattern shows iterative improvements to install.ps1.