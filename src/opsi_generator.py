#!/usr/bin/env python3

import os
import json
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
import zipfile

class OPSIPackageGenerator:
    """Generator für OPSI-Pakete"""
    
    def __init__(self):
        self.template_dir = Path(__file__).parent / "templates"
        
    def generate(self, package_data):
        """
        Generiert ein OPSI-Paket basierend auf den übergebenen Daten
        
        Args:
            package_data (dict): Dictionary mit allen Paket-Informationen
            
        Returns:
            dict: Status und Pfad des generierten Pakets
        """
        try:
            # Output-Verzeichnis erstellen
            output_dir = Path(package_data.get('output_dir', 'C:\\OPSI-Pakete'))
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Paket-Verzeichnis erstellen
            package_id = package_data['id']
            package_version = package_data['version']
            package_name = f"{package_id}_{package_version}"
            package_dir = output_dir / package_name
            
            # Verzeichnisstruktur erstellen
            package_dir.mkdir(exist_ok=True)
            (package_dir / "CLIENT_DATA").mkdir(exist_ok=True)
            (package_dir / "OPSI").mkdir(exist_ok=True)
            
            # control Datei erstellen
            self._create_control_file(package_dir / "OPSI" / "control", package_data)
            
            # Setup-Script erstellen
            self._create_setup_script(package_dir / "CLIENT_DATA" / "setup.opsiscript", package_data)
            
            # Uninstall-Script erstellen
            self._create_uninstall_script(package_dir / "CLIENT_DATA" / "uninstall.opsiscript", package_data)
            
            # Setup-Datei kopieren (falls vorhanden)
            if package_data.get('setup_file') and os.path.exists(package_data['setup_file']):
                setup_file = Path(package_data['setup_file'])
                target_file = package_dir / "CLIENT_DATA" / setup_file.name
                shutil.copy2(setup_file, target_file)
            
            # Paket als ZIP archivieren (optional)
            zip_path = output_dir / f"{package_name}.zip"
            self._create_zip_archive(package_dir, zip_path)
            
            return {
                'success': True,
                'path': str(package_dir),
                'zip_path': str(zip_path)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_control_file(self, file_path, data):
        """Erstellt die OPSI control Datei"""
        control_content = f"""[Package]
version: 1
depends: 
incremental: False

[Product]
type: localboot
id: {data['id']}
name: {data['name']}
description: {data.get('description', data['name'])}
advice: 
version: {data['version']}
priority: {data.get('priority', '0')}
licenseRequired: False
productClasses: 
setupScript: setup.opsiscript
uninstallScript: uninstall.opsiscript
updateScript: 
alwaysScript: 
onceScript: 
customScript: 
userLoginScript: 

[ProductDependency]
"""
        
        # Abhängigkeiten hinzufügen
        if data.get('dependencies'):
            deps = [d.strip() for d in data['dependencies'].split(',')]
            for dep in deps:
                if dep:
                    control_content += f"""action: setup
requiredProduct: {dep}
requiredStatus: installed
requirementType: before

"""
        
        # Windows Version Requirements
        if data.get('min_windows'):
            control_content += f"""
[ProductProperty]
type: unicode
name: min_windows_version
description: Minimum Windows Version
default: {data['min_windows']}
"""
        
        # Architecture Property
        control_content += f"""
[ProductProperty]
type: unicode
name: architecture
multivalue: False
editable: False
description: System Architecture
values: ["32", "64", "both"]
default: ["{self._map_architecture(data.get('architecture', 'x64'))}"]
"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(control_content)
    
    def _create_setup_script(self, file_path, data):
        """Erstellt das Setup-Script"""
        setup_script = f"""; ----------------------------------------------------------------
; Setup script for {data['name']}
; Version: {data['version']}
; Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
; ----------------------------------------------------------------

[Actions]
requiredWinstVersion >= "4.11.6"

DefVar $ProductId$
DefVar $ProductName$
DefVar $Version$
DefVar $MinimumSpace$
DefVar $InstallDir$
DefVar $SetupFile$
DefVar $ExitCode$
DefVar $ErrorMsg$

Set $ProductId$ = "{data['id']}"
Set $ProductName$ = "{data['name']}"
Set $Version$ = "{data['version']}"
Set $MinimumSpace$ = "500 MB"
Set $InstallDir$ = "%ProgramFiles32%\\$ProductName$"
"""
        
        # Setup-Datei definieren
        if data.get('setup_file'):
            setup_filename = Path(data['setup_file']).name
            setup_script += f'Set $SetupFile$ = "%ScriptPath%\\{setup_filename}"\n'
        else:
            setup_script += 'Set $SetupFile$ = "%ScriptPath%\\setup.exe"\n'
        
        setup_script += """
if not(HasMinimumSpace ("%SystemDrive%", $MinimumSpace$))
    LogError "Not enough space on %SystemDrive%, " + $MinimumSpace$ + " on drive %SystemDrive% needed for " + $ProductId$
    isFatalError "No Space"
endif

comment "Show product picture"
ShowBitmap "%ScriptPath%\\" + $ProductId$ + ".png" $ProductName$

Message "Installing " + $ProductId$ + " " + $Version$ + " ..."
"""
        
        # Pre-Install Script
        if data.get('pre_install'):
            setup_script += f"""
comment "Running pre-installation script"
DosInAnIcon_PreInstall
"""
        
        # Installation
        setup_script += f"""
comment "Start setup program"
ChangeDirectory "%ScriptPath%"
"""
        
        if data.get('install_type') == 'msi':
            setup_script += "Winbatch_install_msi\n"
        else:
            setup_script += "Winbatch_install_exe\n"
        
        setup_script += """Sub_check_exitcode

"""
        
        # Post-Install Script  
        if data.get('post_install'):
            setup_script += f"""
comment "Running post-installation script"
DosInAnIcon_PostInstall
"""
        
        # Sections
        if data.get('install_type') == 'msi':
            setup_script += f"""
[Winbatch_install_msi]
msiexec /i "$SetupFile$" {data.get('silent_params', '/quiet /norestart')} 
"""
        else:
            setup_script += f"""
[Winbatch_install_exe]
"$SetupFile$" {data.get('silent_params', '/S')}
"""
        
        # Pre-Install Section
        if data.get('pre_install'):
            setup_script += f"""
[DosInAnIcon_PreInstall]
{data['pre_install']}
"""
        
        # Post-Install Section
        if data.get('post_install'):
            setup_script += f"""
[DosInAnIcon_PostInstall]
{data['post_install']}
"""
        
        # Exit Code Check
        setup_script += """
[Sub_check_exitcode]
comment "Test for installation success via exit code"
set $ExitCode$ = getLastExitCode
; informationen zu Exitcodes siehe
; http://msdn.microsoft.com/en-us/library/aa372835(VS.85).aspx
; http://msdn.microsoft.com/en-us/library/aa368542.aspx
if ($ExitCode$ = "0")
    comment "Looks good: setup program gives exitcode zero"
else
    comment "Setup program gives a exitcode unequal zero: " + $ExitCode$
    if ($ExitCode$ = "1605")
        comment "ERROR_UNKNOWN_PRODUCT 1605 This action is only valid for products that are currently installed."
        comment "Uninstall of a not installed product failed - no problem"
    else
        if ($ExitCode$ = "1641")
            comment "looks good: setup program gives exitcode 1641"
            comment "ERROR_SUCCESS_REBOOT_INITIATED 1641 The installer has initiated a restart. This message is indicative of a success."
        else
            if ($ExitCode$ = "3010")
                comment "looks good: setup program gives exitcode 3010"
                comment "ERROR_SUCCESS_REBOOT_REQUIRED 3010 A restart is required to complete the install. This message is indicative of a success."
            else
                logError "Fatal: Setup program gives an unknown exitcode unequal zero: " + $ExitCode$
                isFatalError
            endif
        endif
    endif
endif
"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(setup_script)
    
    def _create_uninstall_script(self, file_path, data):
        """Erstellt das Uninstall-Script"""
        uninstall_script = f"""; ----------------------------------------------------------------
; Uninstall script for {data['name']}
; Version: {data['version']}
; Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
; ----------------------------------------------------------------

[Actions]
requiredWinstVersion >= "4.11.6"

DefVar $ProductId$
DefVar $ProductName$
DefVar $Version$
DefVar $UninstallProgram$
DefVar $ExitCode$

Set $ProductId$ = "{data['id']}"
Set $ProductName$ = "{data['name']}"
Set $Version$ = "{data['version']}"

comment "Show product picture"
ShowBitmap "%ScriptPath%\\" + $ProductId$ + ".png" $ProductName$

Message "Uninstalling " + $ProductId$ + " ..."
"""
        
        if data.get('uninstall_cmd'):
            uninstall_script += f"""
comment "Uninstall program found, starting uninstall"
Winbatch_uninstall
Sub_check_exitcode

[Winbatch_uninstall]
{data['uninstall_cmd']}
"""
        else:
            # Standard Uninstall über Registry suchen
            uninstall_script += """
if FileExists("%ScriptPath%\\delsub.opsiscript")
    comment "Start uninstall sub section"
    Sub "%ScriptPath%\\delsub.opsiscript"
endif

comment "Searching for uninstall program in registry"
Set $UninstallProgram$ = GetRegistryStringValue32("[HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{" + $ProductId$ + "}] UninstallString")

if not ($UninstallProgram$ = "")
    comment "Uninstall program found, starting uninstall"
    Winbatch_uninstall
    Sub_check_exitcode
endif

[Winbatch_uninstall]
"$UninstallProgram$" /S
"""
        
        # Exit Code Check  
        uninstall_script += """
[Sub_check_exitcode]
comment "Test for installation success via exit code"
set $ExitCode$ = getLastExitCode
if ($ExitCode$ = "0")
    comment "Looks good: setup program gives exitcode zero"
else
    comment "Setup program gives a exitcode unequal zero: " + $ExitCode$
    if ($ExitCode$ = "1605")
        comment "ERROR_UNKNOWN_PRODUCT 1605 This action is only valid for products that are currently installed."
        comment "Uninstall of a not installed product failed - no problem"
    else
        if ($ExitCode$ = "1641")
            comment "looks good: setup program gives exitcode 1641"
            comment "ERROR_SUCCESS_REBOOT_INITIATED 1641"
        else
            if ($ExitCode$ = "3010")
                comment "looks good: setup program gives exitcode 3010"
                comment "ERROR_SUCCESS_REBOOT_REQUIRED 3010"
            else
                logError "Fatal: Setup program gives an unknown exitcode unequal zero: " + $ExitCode$
                isFatalError
            endif
        endif
    endif
endif
"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(uninstall_script)
    
    def _create_zip_archive(self, source_dir, zip_path):
        """Erstellt ein ZIP-Archiv des Pakets"""
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir.parent)
                    zipf.write(file_path, arcname)
    
    def _map_architecture(self, arch):
        """Mappt Architektur-Bezeichnungen"""
        mapping = {
            'x86': '32',
            'x64': '64',
            'both': 'both'
        }
        return mapping.get(arch, '64')

if __name__ == "__main__":
    # Test
    generator = OPSIPackageGenerator()
    test_data = {
        'id': 'test-package',
        'name': 'Test Package',
        'version': '1.0.0',
        'description': 'Ein Test-Paket',
        'vendor': 'Test Vendor',
        'setup_file': 'setup.exe',
        'silent_params': '/S',
        'install_type': 'exe',
        'architecture': 'x64',
        'priority': '0',
        'output_dir': './test_output'
    }
    
    result = generator.generate(test_data)
    print(f"Result: {result}")