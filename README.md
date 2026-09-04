# Discord Proxy

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6?logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-2E8B57)](https://github.com/TomSchimansky/CustomTkinter)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Aplicativo desktop para rotear o Discord por um proxy nos Estados Unidos, ajudando a contornar restricoes regionais e aplicando politicas anti-leak para WebRTC. O relay local injeta autenticacao no proxy upstream sem expor credenciais ao processo do Discord.

## Download Direto (.exe)

Baixe a versao pronta na aba [Releases](https://github.com/Kevin7Denker/Discord-Proxy/releases). O executavel nao exige Python instalado.

## Instalar Pelo Codigo-Fonte

```powershell
git clone https://github.com/Kevin7Denker/Discord-Proxy.git
cd Discord-Proxy
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## Configuracao

- **Host:** endereco DNS ou IP do proxy.
- **Port:** porta TCP do proxy.
- **Type:** `SOCKS5` ou `HTTP`.
- **Username / Password:** credenciais do proxy, quando exigidas.
- **Discord executable:** caminho do `Discord.exe`; o app tenta detectar esse caminho automaticamente.
- **RTC mode:** `media` por padrao para permitir voz e transmissao; use `strict` em `DISCORD_RTC_MODE` somente quando quiser bloquear UDP/WebRTC fora do proxy.
- **Iniciar com Windows:** pode ser ativado em Configuracoes e grava uma entrada no `Run` do usuario atual, sem exigir administrador.

Use **Test connection** para confirmar IP, pais e latencia antes de iniciar o Discord.

## Compilar O Executavel

Instale as dependencias e execute:

```powershell
.venv-build\Scripts\python.exe scripts\build.py
.venv-build\Scripts\python.exe scripts\build_setup.py
```

O arquivo `dist\DiscordProxie-Setup.exe` sera gerado com o aplicativo empacotado. O build usa o `.env` local quando ele existe, para que o instalador leve a rota de proxy configurada sem commitar credenciais. Se `.env` nao existir, o build usa `.env.example` apenas como fallback.

Mantenha `assets/icon.ico` no repositorio para usar o icone personalizado.

## Estrutura

```text
core/       configuracao, proxy, relay e launcher
ui/         splash e dashboard
assets/     recursos visuais
main.py     entrada da aplicacao
build.py    automacao do PyInstaller
```

## Creditos

By Denker
