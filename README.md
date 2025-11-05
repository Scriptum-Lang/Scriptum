# Scriptum Compiler (Python)

Scriptum e uma linguagem com sintaxe inspirada em JavaScript, palavras-chave em latim e tipagem explicita. Este repositorio mantem a toolchain em Python 3.11+, incluindo lexer, parser, analise semantica e builds standalone via PyInstaller.

## Instalacao (sem Python)

1. **Script de instalacao (Linux/macOS)**  
   ```bash
   curl -fsSL https://raw.githubusercontent.com/Scriptum-Lang/Scriptum/main/scripts/install.sh | bash
   ```
   O script detecta seu sistema, baixa o binario `scriptum`, instala em `~/.local/bin` (ou sugere `/usr/local/bin`) e orienta sobre o `PATH`.

2. **Script de instalacao (Windows PowerShell)**  
   ```powershell
   iwr https://raw.githubusercontent.com/Scriptum-Lang/Scriptum/main/scripts/install.ps1 -UseBasicParsing | iex
   ```
   Cria `%LOCALAPPDATA%\Programs\scriptum`, baixa `scriptum.exe` da ultima release e atualiza o `PATH` do usuario se necessario.

3. **Download manual**  
   - Acesse a ultima release em `https://github.com/Scriptum-Lang/Scriptum/releases/latest`.
   - Baixe o binario adequado ao seu sistema.
   - Linux/macOS: `chmod +x scriptum` e mova para uma pasta presente no `PATH` (ex.: `/usr/local/bin` ou `~/.local/bin`).  
   - Windows: copie `scriptum.exe` para um diretorio no `PATH` ou adicione o diretorio aos caminhos de usuario.

## Verificacao

Apos a instalacao, valide:

```bash
scriptum --version
scriptum --help
```

(Use `scriptum.exe` no Windows quando estiver fora do `PATH`.)

## Uso rapido

Experimente o parser com o exemplo incluido:

```bash
scriptum parse examples/hello.stm
```

Tambem e possivel tokenizar (`lex`) ou checar semantica (`sema`) se a build incluir esses subcomandos.

## Suporte de SO

- Linux (glibc x86_64, arm64)
- macOS (Intel e Apple Silicon)
- Windows 10+ (x86_64)

Outros ambientes podem funcionar, mas nao recebem suporte oficial.

## Estado do projeto

Lexer, parser e analise semantica estao estaveis para programas pequenos. A geracao de IR e codegen encontram-se em progresso (WIP); partes da pipeline ainda retornam TODOs ou codigo experimental.

## Build local para dev

1. **Criar ambiente e instalar dependencias**

   - `pipx install poetry` ou `pipx install hatch` (opcional)  
   - Alternativamente, use `python -m venv .venv && source .venv/bin/activate` (Linux/macOS) ou `.venv\Scripts\activate` (Windows).

2. **Instalar o projeto para desenvolvimento**

   ```bash
   pip install -e ".[dev]"
   ```

   ou com `pipx`:

   ```bash
   pipx runpip scriptum install -e ".[dev]"
   ```

3. **Executar PyInstaller (gerando binario local)**

   ```bash
   pyinstaller -F -n scriptum --additional-hooks-dir hooks --collect-data scriptum src/scriptum/driver.py
   ```

   O resultado ficara em `dist/scriptum` (`dist/scriptum.exe` no Windows). Utilize os scripts `scripts/smoke_local.sh` ou `scripts/smoke_local.ps1` para smoke tests rapidos do binario recem-gerado.

Para mais detalhes sobre estrutura de diretorios e documentacao tecnica, consulte a pasta `docs/` e os exemplos em `examples/`.
