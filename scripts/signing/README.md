# Windows Code Signing & Release Automation

Este diretório contém os scripts necessários para gerenciar o ciclo de vida de uma assinatura digital autoassinada no Windows. Com ele, você pode assinar o aplicativo `Discord Proxie` e seu instalador (`setup`), estabelecendo confiança na sua máquina de desenvolvimento.

## ⚠️ Aviso Importante sobre Certificados Autoassinados

* Um certificado autoassinado **adiciona uma assinatura Authenticode válida** ao executável, protegendo-o contra adulterações.
* Ele permite identificar o Publisher (ex: *Kevin Denker*) quando o certificado é explicitamente confiado no computador do usuário.
* É ideal para ambientes internos, desenvolvimento e distribuição inicial controlada.

**Porém:**
* Ele **não possui confiança pública automática**. Computadores de terceiros não confiarão automaticamente nele, diferentemente de um certificado emitido por uma Autoridade Certificadora (CA) paga.
* **Não garante** a remoção dos alertas do Microsoft Defender SmartScreen.
* **Não garante** a aceitação pelo Smart App Control.
* Para não exibir alertas em outros computadores, os usuários precisam instalar o seu `.cer` público manualmente na loja *Trusted People* (Pessoas Confiáveis).

---

## 1. Criar o certificado

Gera um certificado Code Signing (RSA 3072, SHA-256) autoassinado e o armazena no repositório de certificados do seu usuário. Também extrai o arquivo `.cer` público.

```powershell
.\scripts\signing\create-certificate.ps1
```

*(Opcional: Você pode passar a senha do `.pfx` através do parâmetro `-PfxPassword (Read-Host -AsSecureString)` caso precise extrair a chave privada para CI/CD externo).*

## 2. Confiar no certificado localmente

Para que seu próprio computador confie nos `.exe`s gerados por você, instale o `.cer` gerado na loja `CurrentUser\TrustedPeople` (Pessoas Confiáveis). **Nota:** Isso é menos invasivo e mais recomendado do que instalar em `Trusted Root Certification Authorities` (Autoridades de Certificação Raiz Confiáveis).

```powershell
.\scripts\signing\install-certificate.ps1
```

## 3. Gerar release completa

Para automatizar tudo de uma vez: Limpar o cache, buildar via PyInstaller, assinar o `.exe`, criar o Instalador via Inno Setup, assinar o Instalador e validar tudo:

```powershell
.\build-release.ps1
```

*(Lembre-se: Você precisa ter o **Inno Setup 6** instalado no computador para a compilação do setup funcionar. Caso contrário, o script avisará, mas ainda assim fará o build e assinará o executável solto).*

## Assinar manualmente

Se precisar assinar um arquivo avulso:

```powershell
.\scripts\signing\sign.ps1 ".\dist\MeuApp.exe"
```

## Verificar

Para checar os metadados de uma assinatura e garantir que ela é válida:

```powershell
.\scripts\signing\verify-signature.ps1 ".\dist\MeuApp.exe"
```
