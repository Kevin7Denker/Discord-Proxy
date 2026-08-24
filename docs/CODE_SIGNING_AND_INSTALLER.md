# Code Signing and Installer

This project builds a Windows desktop application with PyInstaller, signs the executable with Microsoft Authenticode, packages it with Inno Setup, signs the installer, and verifies both signatures.

## Project Summary

- Product name: `Discord Proxy`
- Publisher: `Discord Proxy Tools`
- Version: `1.0.0`
- Main executable: `dist\DiscordProxy.exe`
- Installer: `dist\DiscordProxy-Setup.exe`
- Installer technology: Inno Setup 6
- Runtime user configuration: `%LOCALAPPDATA%\Discord Proxy\config.json`
- Install location: `%ProgramFiles%\Discord Proxy Tools\Discord Proxy`

## Build

Install Python dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Build the executable:

```powershell
python build.py
```

Expected output:

```text
dist\DiscordProxy.exe
```

The build uses `assets\icon.ico` and `version_info.txt` for Windows executable metadata.

## Installer

Install Inno Setup 6 from the official Inno Setup website. The release script can find `ISCC.exe` from PATH or the default installation directories.

If Inno Setup is installed elsewhere, configure:

```powershell
$env:INNOSETUP_COMPILER = "C:\Path\To\Inno Setup 6\ISCC.exe"
```

Build the installer manually after building and signing the app executable:

```powershell
ISCC.exe installer\installer.iss
```

Expected output:

```text
dist\DiscordProxy-Setup.exe
```

The installer creates Start Menu entries, an uninstaller, Installed Apps metadata, and an optional desktop shortcut.

## Code Signing

Install the Windows SDK so `signtool.exe` is available. The scripts search PATH first, then common Windows Kit locations.

Production signing should use a public Code Signing certificate trusted by Windows, preferably backed by a hardware token, HSM, Cloud HSM, or cloud signing provider. Do not commit certificate files, private keys, PINs, passwords, or signing service credentials.

Configure production certificate selection by thumbprint:

```powershell
$env:CODESIGN_CERT_THUMBPRINT = "0123456789ABCDEF0123456789ABCDEF01234567"
$env:CODESIGN_TIMESTAMP_SERVER = "http://timestamp.digicert.com"
```

Or by subject when thumbprint selection is not practical:

```powershell
$env:CODESIGN_CERT_SUBJECT = "Your Company Name"
```

Sign one file:

```powershell
.\scripts\sign.ps1 .\dist\DiscordProxy.exe
```

The script uses SHA-256 and RFC 3161 timestamping:

```text
signtool sign /fd SHA256 /tr <timestamp server> /td SHA256
```

## Development Certificate

For local testing only, create a self-signed code signing certificate:

```powershell
New-SelfSignedCertificate `
  -Type CodeSigningCert `
  -Subject "CN=Discord Proxy Development" `
  -CertStoreLocation Cert:\CurrentUser\My
```

Then set:

```powershell
$env:CODESIGN_CERT_SUBJECT = "Discord Proxy Development"
```

Use development signing only for internal local testing:

```powershell
.\scripts\release.ps1 -Configuration Development
```

Self-signed certificates are not appropriate for public releases and will not build public reputation with SmartScreen or Smart App Control.

## Production Release

Configure production signing first:

```powershell
$env:CODESIGN_CERT_THUMBPRINT = "0123456789ABCDEF0123456789ABCDEF01234567"
$env:CODESIGN_TIMESTAMP_SERVER = "http://timestamp.digicert.com"
```

Then run:

```powershell
.\scripts\release.ps1
```

Release flow:

```text
clean previous build
build DiscordProxy.exe
sign DiscordProxy.exe
verify DiscordProxy.exe
build DiscordProxy-Setup.exe
sign DiscordProxy-Setup.exe
verify DiscordProxy-Setup.exe
```

## Verification

Verify the application executable:

```powershell
.\scripts\verify-signature.ps1 .\dist\DiscordProxy.exe
Get-AuthenticodeSignature .\dist\DiscordProxy.exe
```

Verify the installer:

```powershell
.\scripts\verify-signature.ps1 .\dist\DiscordProxy-Setup.exe
Get-AuthenticodeSignature .\dist\DiscordProxy-Setup.exe
```

Expected PowerShell status:

```text
Status: Valid
```

You can also inspect:

```text
File Properties -> Digital Signatures
```

## Clean Install Test

On a clean Windows VM:

1. Copy only `dist\DiscordProxy-Setup.exe`.
2. Run the installer normally.
3. Confirm files are installed under `%ProgramFiles%\Discord Proxy Tools\Discord Proxy`.
4. Press the Windows key and search for `Discord Proxy`.
5. Confirm `Settings -> Apps -> Installed apps` shows `Discord Proxy`, publisher, and version.
6. Launch the app from the Start Menu.
7. Confirm user settings are written under `%LOCALAPPDATA%\Discord Proxy`.
8. Uninstall from Installed Apps.
9. Confirm program files are removed. User configuration may remain unless intentionally removed by a future data-cleanup option.

## Troubleshooting

- SignTool not found: install the Windows SDK or add the Windows Kits `x64` folder to PATH.
- Certificate not found: verify `CODESIGN_CERT_THUMBPRINT` or `CODESIGN_CERT_SUBJECT`.
- Timestamp unavailable: check network access and `CODESIGN_TIMESTAMP_SERVER`.
- Invalid signature: make sure the file was not modified after signing.
- Token disconnected: reconnect the USB token and confirm middleware is running.
- Incorrect PIN: unlock the token using the vendor tool; do not store the PIN in Git or scripts.
- Installer not found: install Inno Setup 6 or set `INNOSETUP_COMPILER`.
- SmartScreen: use a trusted public Code Signing certificate and build reputation over time.
- Smart App Control: do not bypass Windows protections; distribute a signed, timestamped installer from a reputable channel.
