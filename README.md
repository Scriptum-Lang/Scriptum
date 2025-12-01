# Scriptum Compiler (Python)

Scriptum e uma linguagem com sintaxe inspirada em JavaScript, palavras-chave em latim e tipagem explicita. Este repositorio mantem a toolchain em Python 3.11+, incluindo lexer, parser, analise semantica e builds standalone via PyInstaller.

## Instalacao (sem Python)

1. **Script de instalacao (Linux/macOS)**  
   ```bash
   curl -fsSL https://raw.githubusercontent.com/Scriptum-Lang/Scriptum/main/scripts/install.sh | bash
   ```
   O script detecta seu sistema, baixa o binario `scriptum`, instala em `~/.local/bin` (ou sugere `/usr/local/bin`) e orienta sobre o `PATH`. Se ja existir um `scriptum` em `~/.local/bin`, ele sera substituido pela nova versao; caso outra instalacao seja encontrada em um diretorio diferente, o instalador exibe um aviso, pergunta se voce deseja remover a copia antiga e recomenda ajustar o `PATH` se necessario.

2. **Script de instalacao (Windows PowerShell)**  
   ```powershell
   iwr https://raw.githubusercontent.com/Scriptum-Lang/Scriptum/main/scripts/install.ps1 -UseBasicParsing | iex
   ```
   Cria `%LOCALAPPDATA%\Programs\scriptum`, baixa `scriptum.exe` da ultima release e atualiza o `PATH` do usuario se necessario.

3. **Download manual**  
   - Acesse a ultima release em `https://github.com/Scriptum-Lang/Scriptum/releases/latest`.
   - Baixe o binario adequado ao seu sistema (`scriptum-vX.Y.Z-linux`, `scriptum-vX.Y.Z-macos`, `scriptum-vX.Y.Z-windows.exe`).
   - Linux/macOS: renomeie para `scriptum`, execute `chmod +x scriptum` e mova para um diretorio presente no `PATH` (ex.: `/usr/local/bin` ou `~/.local/bin`).  
   - Windows: renomeie o arquivo para `scriptum.exe`, copie para um diretorio no `PATH` ou adicione o diretorio aos caminhos de usuario.

## Verificacao

Apos a instalacao, valide:

```bash
scriptum --version
scriptum --help
```

(Use `scriptum.exe` no Windows quando estiver fora do `PATH`.)

## Uso rápido

Alguns exemplos rápidos:

```bash
# executa diretamente um arquivo .stm (interpretação padrão)
scriptum run examples/hello.stm

# executa com o backend de bytecode experimental (stack VM em Python)
scriptum run --backend=bytecode examples/hello.stm

# força o backend LLVM textual (recai na VM se llvm-as/lli não estiverem disponíveis)
scriptum run --backend=llvm examples/hello.stm

# usa o backend LLVM em C++ (pybind11 + fallback para a VM se não houver biblioteca)
scriptum run --backend=llvm-cpp examples/hello.stm

# seleciona o backend desejado via variável de ambiente (vm, bytecode, llvm, llvm-cpp)
export SCRIPTUM_BACKEND=llvm
scriptum run examples/hello.stm

# impede fallback para a VM quando o backend escolhido falhar
scriptum run --backend=llvm --strict-backend examples/hello.stm

# executa código inline e módulos
scriptum -c "redde 42;"
scriptum run -m exemplos.basico

# ferramentas úteis
scriptum check examples/err/type_mismatch.stm --json
scriptum fmt examples/ok/control_flow.stm
scriptum dev lex examples/hello.stm
scriptum dev llvm examples/hello.stm --verify
```

Consulte `docs/wiki/14_keywords.md` para a lista completa de palavras-chave e
comandos reconhecidos pela linguagem.

Todos os utilitários de inspeção (lexer, AST, IR, geração de tabelas) vivem agora em `scriptum dev <subcomando>`.

Os comandos `run`/`build` também aceitam a variável `SCRIPTUM_BACKEND` (`vm` ou `llvm`) para definir o backend padrão e `SCRIPTUM_BACKEND_STRICT=1` (ou `--strict-backend`) caso deseje falhar imediatamente quando o backend escolhido não estiver disponível e evitar o fallback automático para a VM.

## Suporte de SO

- Linux (glibc x86_64, arm64)
- macOS (Intel e Apple Silicon)
- Windows 10+ (x86_64)

Outros ambientes podem funcionar, mas nao recebem suporte oficial.

## Estado do projeto

Lexer, parser e analise semantica estao estaveis para programas pequenos. A geracao de IR e codegen encontram-se em progresso (WIP); partes da pipeline ainda retornam TODOs ou codigo experimental. O backend LLVM textual atual utiliza um runtime em C (veja `src/scriptum/runtime/`) e é desenvolvido em paralelo ao CLI; os artifacts de IR podem ser obtidos via `scriptum build --emit llvm` e validados com `--verify-llvm` (usa `llvm-as` quando disponível), enquanto a integração de execução com `lli` continua em andamento.

### Backends experimentais

#### Bytecode (stack VM em Python)

- scriptum run --backend=bytecode executa o IR estrutural em uma pequena VM de bytecode. O compilador (scriptum.bytecode) converte ModuleIr em instruções de pilha (PUSH_CONST, JUMP, CALL, etc.) e o interpretador (BytecodeVM) reusa as implementações dos builtins existentes.
- A suíte dedicada vive em tests/test_bytecode_backend.py e abrange retornos literais, loops (dum, frange, perge) e chamadas para summa. Rode python -m pytest tests/test_bytecode_backend.py.
- scriptum build --backend bytecode --emit bytecode imprime uma listagem textual das instruções (útil para depuração).

#### LLVM textual + runtime em C

- O runtime mora em src/scriptum/runtime/ (declarações em runtime.h, implementação em llvm_rt.c). Ele expõe scriptum_value (variant usado pelo gerador) e helpers para textos, arrays, objetos, opcionais e lambdas.
- Utilize scripts/build_runtime.sh para compilar llvm_rt.c em build/libscriptum_rt.{a,so} (o script escolhe automaticamente .dll no Windows). Passe CC=<compiler> e/ou CFLAGS para configurações customizadas.
- Testes básicos podem ser executados com python -m pytest tests/test_runtime_llvm.py, que compila a biblioteca compartilhada em diretório temporário e valida construtores/arrays/textos via ctypes. O teste será ignorado automaticamente caso não exista um compilador C acessível.
- O gerador LLVM (scriptum.codegen.llvm) opera integralmente sobre scriptum_value, internando textos e delegando arrays/objetos ao runtime. Os testes de geração (python -m pytest tests/test_llvm_codegen.py) cobrem funções, dum, pro in, arrays, strings e ??.
- Há uma suíte de snapshots em tests/backend_llvm/ (ex.: basic_valid, loops) que garante estabilidade do IR textual; execute python -m pytest tests/backend_llvm para validar.
- scriptum build --emit llvm --verify-llvm e scriptum dev llvm --verify executam llvm-as (quando disponível) para validar o IR emitido e reportam erros amigáveis caso o binário não esteja instalado; ao definir SCRIPTUM_BACKEND=llvm, scriptum build passa a emitir LLVM por padrão.
- scriptum run --backend=llvm (ou SCRIPTUM_BACKEND=llvm) compila automaticamente o runtime, gera o IR textual, invoca lli com uma ponte que serializa o resultado em JSON e volta para a VM quando lli ou o compilador C não estiverem disponíveis (avisando o usuário). Passe --strict-backend ou defina SCRIPTUM_BACKEND_STRICT=1 para falhar imediatamente caso o backend não consiga ser usado.

#### LLVM C++ (pybind11 + GoogleTest)

- cpp/llvm_codegen/ abriga o backend em C++: um emissor mínimo (scriptum::SimpleModuleEmitter) que gera llvm::Module para funções que retornam literais ou somas de literais, os bindings em pybind11 (scriptum_codegen_llvm_cpp_py) e a suíte do GoogleTest (tests/SimpleModuleTests.cpp).
- Use python scripts/build_cpp_backend.py para configurar/compilar o backend e rodar os testes (cmake + llvm-config precisam estar disponíveis). O script detecta automaticamente LLVM_DIR/llvm-config e ignora o build quando o toolchain não estiver instalado.
- Após o build, a CLI localiza automaticamente a biblioteca em cpp/llvm_codegen/build. Caso use outro diretório, defina SCRIPTUM_LLVM_CPP_PATH apontando para a pasta que contém scriptum_codegen_llvm_cpp_py.*.
- scriptum run --backend=llvm-cpp reutiliza o mesmo pipeline do backend textual: gera o módulo em C++, serializa para LLVM IR, invoca lli e retorna o resultado em JSON. Quando o binding não estiver disponível, o CLI recai para a VM (a menos que --strict-backend esteja ativo).
- scriptum build --backend llvm-cpp --emit llvm usa o emissor em C++ para gerar o IR textual, permitindo comparar facilmente as saídas dos dois backends.

#### Requisitos dos backends

- **VM estrutural**: sem dependências extras. Este é o backend padrão.
- **Bytecode**: roda inteiramente em Python; nenhuma ferramenta adicional é necessária.
- **LLVM textual**:
  1. Compilador C acessível (cc, clang ou gcc). O CLI compila src/scriptum/runtime/llvm_rt.c on-demand; ajuste CC se precisar de um binário específico.
  2. llvm-as para verificar o IR textual (opcional, mas recomendado).
  3. lli para executar o IR quando --backend=llvm for escolhido.
  4. Opcionalmente, defina as variáveis LLVM_AS ou LLI apontando para os executáveis caso eles não estejam no PATH.
- **LLVM C++**:
  1. Toolchain C++ (cmake + compilador) e as bibliotecas do LLVM disponíveis via LLVM_DIR ou llvm-config.
  2. pybind11 e o GoogleTest são baixados automaticamente pelo CMake via FetchContent.
  3. Execute python scripts/build_cpp_backend.py para gerar scriptum_codegen_llvm_cpp_py.* e scriptum_codegen_llvm_cpp_tests em cpp/llvm_codegen/build. A CLI procura automaticamente o módulo nesse diretório; use SCRIPTUM_LLVM_CPP_PATH para apontar para builds personalizados.

Quando alguma ferramenta estiver ausente, o CLI exibe uma mensagem clara e recai automaticamente para a VM estrutural (a menos que --strict-backend/SCRIPTUM_BACKEND_STRICT=1 tenham sido ativados).

## Build local para dev

1. **Sincronizar dependencias com uv**

   ```bash
   uv venv                      # cria .venv/
   uv sync --extra dev          # instala deps + ferramentas (pytest, black, pyinstaller, etc.)
   ```

   Nao e necessario ativar manualmente a venv; basta prefixar os comandos com `uv run`.

2. **Gerar o binario standalone**

   ```bash
   uv run scriptum package
   ```

   O comando gera automaticamente `build/scriptum.spec` apontando para o CLI moderno (`python -m scriptum`), executa o PyInstaller e coloca o artefato em `dist/scriptum` (`dist/scriptum.exe` no Windows). Utilize `scripts/smoke_local.sh` ou `scripts/smoke_local.ps1` para validações rápidas. Caso precise ajustar a spec manualmente, use `uv run scriptum package --spec caminho/customizado.spec`.

Para mais detalhes sobre estrutura de diretorios e documentacao tecnica, consulte a pasta `docs/` e os exemplos em `examples/`.
