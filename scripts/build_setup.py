from __future__ import annotations

from pathlib import Path
import subprocess
import textwrap
import zipfile


APP_NAME = "Discord Proxie"
EXE_NAME = "DiscordProxie.exe"
SETUP_NAME = "DiscordProxie-Setup.exe"


def zip_app(app_dir: Path, payload_zip: Path) -> None:
    payload_zip.parent.mkdir(parents=True, exist_ok=True)
    if payload_zip.exists():
        payload_zip.unlink()
    with zipfile.ZipFile(payload_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in app_dir.rglob("*"):
            if file_path.is_file():
                archive.write(file_path, file_path.relative_to(app_dir))


def write_install_script(path: Path) -> None:
    path.write_text(
        textwrap.dedent(
            f"""
            $ErrorActionPreference = "Stop"

            $installRoot = Join-Path $env:LOCALAPPDATA "Programs\\{APP_NAME}"
            $payload = Join-Path $PSScriptRoot "payload.zip"
            $exePath = Join-Path $installRoot "{EXE_NAME}"

            if (Test-Path $installRoot) {{
              Remove-Item -LiteralPath $installRoot -Recurse -Force
            }}
            New-Item -ItemType Directory -Path $installRoot -Force | Out-Null
            Expand-Archive -LiteralPath $payload -DestinationPath $installRoot -Force

            $shell = New-Object -ComObject WScript.Shell
            $desktopShortcut = Join-Path ([Environment]::GetFolderPath("Desktop")) "{APP_NAME}.lnk"
            $shortcut = $shell.CreateShortcut($desktopShortcut)
            $shortcut.TargetPath = $exePath
            $shortcut.WorkingDirectory = $installRoot
            $shortcut.Save()

            $programsDir = [Environment]::GetFolderPath("Programs")
            $startMenuShortcut = Join-Path $programsDir "{APP_NAME}.lnk"
            $shortcut = $shell.CreateShortcut($startMenuShortcut)
            $shortcut.TargetPath = $exePath
            $shortcut.WorkingDirectory = $installRoot
            $shortcut.Save()

            Start-Process -FilePath $exePath
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )


def write_sed(path: Path, source_dir: Path, output_exe: Path) -> None:
    path.write_text(
        textwrap.dedent(
            f"""
            [Version]
            Class=IEXPRESS
            SEDVersion=3

            [Options]
            PackagePurpose=InstallApp
            ShowInstallProgramWindow=0
            HideExtractAnimation=1
            UseLongFileName=1
            InsideCompressed=0
            CAB_FixedSize=0
            CAB_ResvCodeSigning=0
            RebootMode=N
            InstallPrompt=
            DisplayLicense=
            FinishMessage=
            TargetName={output_exe}
            FriendlyName={APP_NAME}
            AppLaunched=powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -NoProfile -File install.ps1
            PostInstallCmd=<None>
            AdminQuietInstCmd=
            UserQuietInstCmd=
            SourceFiles=SourceFiles

            [SourceFiles]
            SourceFiles0={source_dir}

            [SourceFiles0]
            payload.zip=
            install.ps1=
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )


def build_setup() -> Path:
    root = Path(__file__).resolve().parent.parent
    app_dir = root / "dist" / "DiscordProxie"
    if not (app_dir / EXE_NAME).is_file():
        raise FileNotFoundError(f"Build output not found: {app_dir / EXE_NAME}")

    setup_work_dir = root / "build" / "setup"
    output_exe = root / "dist" / SETUP_NAME
    payload_zip = setup_work_dir / "payload.zip"
    install_script = setup_work_dir / "install.ps1"
    sed_file = setup_work_dir / "iexpress.sed"

    zip_app(app_dir, payload_zip)
    write_install_script(install_script)
    write_sed(sed_file, setup_work_dir, output_exe)

    subprocess.run(["iexpress.exe", "/N", str(sed_file)], check=True)
    return output_exe


if __name__ == "__main__":
    setup_path = build_setup()
    print(f"Setup generated: {setup_path}")
