#![forbid(unsafe_code)]
#![deny(unused_must_use)]

use std::fs;
use std::path::{Path, PathBuf};

use clap::{Parser, Subcommand};
use miette::{Report, Result};

use scriptum_codegen::{emit_module, lower_module, optimize_module};
use scriptum_lexer::{lex, TokenKind};
use scriptum_parser_ll::parse_module;
use scriptum_runtime::{load_module, VirtualMachine};
use scriptum_sema::analyze_module;
use scriptum_utils::{Error, ErrorKind};

#[derive(Parser)]
#[command(name = "scriptum", about = "Compilador Scriptum CLI", version)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Realiza a análise léxica de um arquivo .stm
    Lex { input: PathBuf },
    /// Analisa e imprime a AST
    Parse { input: PathBuf },
    /// Executa a análise semântica
    Sema { input: PathBuf },
    /// Compila arquivo Scriptum para bytecode .sbc
    Build {
        input: PathBuf,
        #[arg(short, long)]
        output: PathBuf,
    },
    /// Executa arquivo .stm ou .sbc
    Run { input: PathBuf },
    /// Valida rapidamente (lex+parse+sema)
    Check { input: PathBuf },
    /// Formata arquivo (stub)
    Fmt { input: PathBuf },
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.command {
        Commands::Lex { input } => run_lex(&input),
        Commands::Parse { input } => run_parse(&input),
        Commands::Sema { input } => run_sema(&input),
        Commands::Build { input, output } => run_build(&input, &output),
        Commands::Run { input } => run_run(&input),
        Commands::Check { input } => run_check(&input),
        Commands::Fmt { input } => run_fmt(&input),
    }
}

fn read_source(path: &Path) -> Result<String> {
    fs::read_to_string(path).map_err(|err| {
        Report::new(Error::with_source(
            ErrorKind::Runtime,
            format!("falha ao ler {}", path.display()),
            err,
        ))
    })
}

fn write_bytes(path: &Path, bytes: &[u8]) -> Result<()> {
    fs::write(path, bytes).map_err(|err| {
        Report::new(Error::with_source(
            ErrorKind::Runtime,
            format!("falha ao escrever {}", path.display()),
            err,
        ))
    })
}

fn run_lex(path: &PathBuf) -> Result<()> {
    let source = read_source(path)?;
    let tokens = lex(&source).map_err(|err| Error::new(ErrorKind::Lexico, err.message))?;
    for token in tokens {
        println!(
            "{:?} {:?}",
            token.kind,
            &source[token.span.start()..token.span.end()]
        );
        if token.kind == TokenKind::EOF {
            break;
        }
    }
    Ok(())
}

fn run_parse(path: &PathBuf) -> Result<()> {
    let source = read_source(path)?;
    let module =
        parse_module(&source).map_err(|err| Error::new(ErrorKind::Sintatico, err.message))?;
    println!("funções parseadas: {}", module.functions.len());
    Ok(())
}

fn run_sema(path: &PathBuf) -> Result<()> {
    let source = read_source(path)?;
    let module =
        parse_module(&source).map_err(|err| Error::new(ErrorKind::Sintatico, err.message))?;
    analyze_module(&module).map_err(|err| Error::new(ErrorKind::Semantico, err.message))?;
    println!("análise semântica concluída");
    Ok(())
}

fn run_build(input: &PathBuf, output: &PathBuf) -> Result<()> {
    let source = read_source(input)?;
    let module =
        parse_module(&source).map_err(|err| Error::new(ErrorKind::Sintatico, err.message))?;
    analyze_module(&module).map_err(|err| Error::new(ErrorKind::Semantico, err.message))?;
    let mut ir = lower_module(&module);
    optimize_module(&mut ir);
    let bytes = emit_module(&ir);
    write_bytes(output, &bytes)?;
    println!("bytecode gerado em {}", output.display());
    Ok(())
}

fn run_run(input: &PathBuf) -> Result<()> {
    let path_str = input.to_string_lossy();
    if path_str.ends_with(".sbc") {
        let chunk =
            load_module(input).map_err(|err| Error::new(ErrorKind::Runtime, err.to_string()))?;
        let vm = VirtualMachine::new(&chunk);
        let result = vm
            .run(0, &[])
            .map_err(|err| Error::new(ErrorKind::Runtime, err.to_string()))?;
        println!("resultado: {}", result.value);
        return Ok(());
    }

    let source = read_source(input)?;
    let module =
        parse_module(&source).map_err(|err| Error::new(ErrorKind::Sintatico, err.message))?;
    analyze_module(&module).map_err(|err| Error::new(ErrorKind::Semantico, err.message))?;
    let mut ir = lower_module(&module);
    optimize_module(&mut ir);
    let bytes = emit_module(&ir);
    let chunk = scriptum_runtime::bytecode::Chunk::from_bytes(&bytes)
        .map_err(|err| Error::new(ErrorKind::Runtime, err.to_string()))?;
    let vm = VirtualMachine::new(&chunk);
    let result = vm
        .run(0, &[])
        .map_err(|err| Error::new(ErrorKind::Runtime, err.to_string()))?;
    println!("resultado: {}", result.value);
    Ok(())
}

fn run_check(path: &PathBuf) -> Result<()> {
    run_sema(path)
}

fn run_fmt(path: &PathBuf) -> Result<()> {
    println!("fmt ainda não implementado para {}", path.display());
    Ok(())
}
