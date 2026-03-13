# OPSI PackForge

Web-based OPSI package builder for paedML Linux.

**https://elliot-markus-john-adams.github.io/opsi-packforge**

## Features

- Create complete OPSI package structure in browser
- Drag & drop installer files
- Auto-detects installer type (MSI, InnoSetup, NSIS, InstallShield, PowerShell)
- Editable install parameters
- Full control file support:
  - Package dependencies (`[ProductDependency]`)
  - Configurable properties (`[ProductProperty]`)
  - All script types (setup, uninstall, update, always, once, custom, userlogin)
  - preinst/postinst scripts
- Edit all files before download
- Download as ready-to-use .zip

## Usage

1. Open the web app
2. Fill in package info (ID, name, version)
3. Select installer type
4. Drag & drop your installer files
5. Add dependencies/properties if needed
6. Click **Build**
7. Edit scripts as needed (click to edit)
8. Click **Download .zip**

## Deploying to OPSI Server

```bash
# Extract and copy to workbench
unzip mypackage.zip -d /var/lib/opsi/workbench/

# Build and install
cd /var/lib/opsi/workbench/mypackage
opsi-makepackage
opsi-package-manager -i mypackage_1.0-1.opsi
```

## Silent Install Parameters

| Installer | Parameters |
|-----------|------------|
| MSI | `msiexec /i /qn /norestart` |
| InnoSetup | `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /ALLUSERS` |
| NSIS | `/S` |
| InstallShield | `/s /sms` |

## Control File Structure

```
[Package]
version: 1
depends:

[Product]
type: localboot
id: mypackage
name: My Package
description: Description here
advice: Usage notes
version: 1.0
priority: 0
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
action: setup
requiredProduct: javavm
requiredStatus: installed
requirementType: before

[ProductProperty]
type: unicode
name: install_mode
description: Installation mode
values: ["standard", "custom"]
default: ["standard"]
```

## License

MIT License
