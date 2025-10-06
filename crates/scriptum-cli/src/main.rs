#![forbid(unsafe_code)]
#![deny(unused_must_use)]

use std::fs;
use std::path::{Path, PathBuf};

use clap::{Parser, Subcommand};
use miette::{Context, IntoDiagnostic, Result};
use scriptum_codegen::generate;
use scriptum_lexer::lex;
use scriptum_parser::{parse_module, ParseOutput};
use scriptum_types::check_module;

/// Ferramenta de linha de comando oficial da linguagem Scriptum.
#[derive(Parser)]
#[command(name = "scriptum", version, about = "Compilador Scriptum CLI")]
struct Cli {
    /// Emite diagnósticos em JSON estruturado
    #[arg(long)]
    json: bool,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Executa o lexer e lista os tokens do arquivo
    Lex { input: PathBuf },
    /// Realiza parsing e exibe o resultado
    Parse { input: PathBuf },
    /// Exibe a AST em JSON
    Ast { input: PathBuf },
    /// Executa análise semântica e de tipos
    Check { input: PathBuf },
    /// Gera código formatado (pretty-printer)
    Build {
        input: PathBuf,
        #[arg(short, long)]
        output: Option<PathBuf>,
    },
    /// Formata o arquivo de entrada (idempotente)
    Fmt {
        input: PathBuf,
        #[arg(long)]
        write: bool,
    },
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.command {
        Commands::Lex { input } => run_lex(&input, cli.json),
        Commands::Parse { input } => run_parse(&input, cli.json),
        Commands::Ast { input } => run_ast(&input),
        Commands::Check { input } => run_check(&input, cli.json),
        Commands::Build { input, output } => run_build(&input, output),
        Commands::Fmt { input, write } => run_fmt(&input, write),
    }
}

fn read_source(path: &Path) -> Result<String> {
    fs::read_to_string(path)
        .into_diagnostic()
        .with_context(|| format!("falha ao ler {}", path.display()))
}

fn run_lex(path: &Path, json: bool) -> Result<()> {
    let source = read_source(path)?;
    let tokens = lex(&source).into_diagnostic()?;
    if json {
        let json = serde_json::to_string_pretty(&tokens).into_diagnostic()?;
        println!("{}", json);
    } else {
        for token in tokens {
            println!("{:?} @{:?}", token.kind, token.span);
        }
    }
    Ok(())
}

fn run_parse(path: &Path, json: bool) -> Result<()> {
    let source = read_source(path)?;
    let output = parse_module(&source).into_diagnostic()?;
    emit_parse_output(&output, json)
}

fn run_ast(path: &Path) -> Result<()> {
    let source = read_source(path)?;
    let output = parse_module(&source).into_diagnostic()?;
    let json = serde_json::to_string_pretty(&output.module).into_diagnostic()?;
    println!("{}", json);
    Ok(())
}

fn run_check(path: &Path, json: bool) -> Result<()> {
    let source = read_source(path)?;
    let output = parse_module(&source).into_diagnostic()?;
    if !output.diagnostics.is_empty() {
        emit_parse_output(&output, json)?;
        return Err(miette::miette!("falha na etapa de parsing"));
    }
    let result = check_module(&output.module);
    if json {
        let json = serde_json::to_string_pretty(&result).into_diagnostic()?;
        println!("{}", json);
    } else if result.diagnostics.is_empty() {
        println!("análise de tipos concluída sem erros");
    } else {
        for diag in &result.diagnostics {
            eprintln!("[{}] {} @{:?}", diag.code, diag.message, diag.span);
        }
    }
    if result.diagnostics.is_empty() {
        Ok(())
    } else {
        Err(miette::miette!("falha na análise de tipos"))
    }
}

fn run_build(path: &Path, output: Option<PathBuf>) -> Result<()> {
    let source = read_source(path)?;
    let output_module = parse_module(&source).into_diagnostic()?;
    if !output_module.diagnostics.is_empty() {
        emit_parse_output(&output_module, false)?;
        return Err(miette::miette!("falha na etapa de parsing"));
    }
    let codegen = generate(&output_module.module);
    if let Some(out_path) = output {
        if let Some(parent) = out_path.parent() {
            fs::create_dir_all(parent).into_diagnostic()?;
        }
        fs::write(&out_path, codegen.formatted.as_bytes())
            .into_diagnostic()
            .with_context(|| format!("falha ao escrever {}", out_path.display()))?;
        println!("código gerado em {}", out_path.display());
    } else {
        print!("{}", codegen.formatted);
    }
    Ok(())
}

fn run_fmt(path: &Path, write: bool) -> Result<()> {
    let source = read_source(path)?;
    let output = parse_module(&source).into_diagnostic()?;
    if !output.diagnostics.is_empty() {
        emit_parse_output(&output, false)?;
        return Err(miette::miette!("falha na etapa de parsing"));
    }
    let codegen = generate(&output.module);
    if write {
        fs::write(path, codegen.formatted.as_bytes())
            .into_diagnostic()
            .with_context(|| format!("falha ao escrever {}", path.display()))?;
    } else {
        print!("{}", codegen.formatted);
    }
    Ok(())
}

fn emit_parse_output(output: &ParseOutput, json: bool) -> Result<()> {
    if json {
        let json = serde_json::to_string_pretty(output).into_diagnostic()?;
        println!("{}", json);
    } else {
        for diag in &output.diagnostics {
            eprintln!("[parse] {} @{:?}", diag.message, diag.span);
        }
        println!("itens parseados: {}", output.module.items.len());
    }
    Ok(())
}
