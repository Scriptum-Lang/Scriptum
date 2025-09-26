use std::env;
use std::fs;
use std::path::{Path, PathBuf};

#[path = "../charclass.rs"]
mod charclass;
#[path = "../hopcroft.rs"]
mod hopcroft;
#[path = "../nfa.rs"]
mod nfa;
#[path = "../pipeline.rs"]
mod pipeline;
#[path = "../regex_ast.rs"]
mod regex_ast;
#[path = "../regex_parse.rs"]
mod regex_parse;
#[path = "../spec.rs"]
mod spec;
#[path = "../subset.rs"]
mod subset;

use pipeline::{build_tokens, BuiltToken};
use spec::{build_token_definitions, parse_spec};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let manifest_dir = PathBuf::from(env::var("CARGO_MANIFEST_DIR")?);
    let spec_path = manifest_dir.join("../../../gramatica_formal.md");
    let diagrams_path = manifest_dir.join("diagrams/afd.md");
    let out_dir = PathBuf::from(env::var("OUT_DIR")?);

    println!("cargo:rerun-if-changed={}", spec_path.display());

    let spec_content = fs::read_to_string(&spec_path)?;
    let spec_data = parse_spec(&spec_content);
    let definitions = build_token_definitions(&spec_data);
    let built = build_tokens(&definitions)?;

    write_keywords(&out_dir, &spec_data.keywords)?;
    write_token_specs(&out_dir, &definitions)?;
    write_token_dfas(&out_dir, &built)?;
    write_class_count(&out_dir)?;

    let emit_diagrams = env::var("SCRIPTUM_EMIT_DIAGRAMS").is_ok();
    if emit_diagrams {
        let content = spec::render_mermaid(&definitions, &built);
        if let Some(parent) = diagrams_path.parent() {
            fs::create_dir_all(parent)?;
        }
        fs::write(&diagrams_path, content)?;
    } else if !diagrams_path.exists() {
        if let Some(parent) = diagrams_path.parent() {
            fs::create_dir_all(parent)?;
        }
        fs::write(&diagrams_path, "# DFAs (gerar com --emit-diagrams)\n")?;
    }

    print_summary(&built, &diagrams_path);

    Ok(())
}

fn write_keywords(out_dir: &Path, keywords: &[String]) -> Result<(), Box<dyn std::error::Error>> {
    let path = out_dir.join("keywords.rs");
    let data = format!("&{:?}", keywords);
    fs::write(path, data)?;
    Ok(())
}

fn write_token_specs(
    out_dir: &Path,
    defs: &[pipeline::TokenDefinition],
) -> Result<(), Box<dyn std::error::Error>> {
    let path = out_dir.join("token_specs.rs");
    let mut buffer = String::new();
    buffer.push_str("&[\n");
    for def in defs {
        buffer.push_str(&format!(
            "    crate::tokens::types::TokenRegex {{ name: {:?}, pattern: {:?}, discard: {}, priority: {} }},\n",
            def.name, def.pattern, def.discard, def.priority
        ));
    }
    buffer.push_str("]\n");
    fs::write(path, buffer)?;
    Ok(())
}

fn write_token_dfas(
    out_dir: &Path,
    built: &[BuiltToken],
) -> Result<(), Box<dyn std::error::Error>> {
    let path = out_dir.join("token_dfas.rs");
    let mut buffer = String::new();
    buffer.push_str("&[\n");
    for (index, token) in built.iter().enumerate() {
        let transitions = flatten_transitions(&token.dfa);
        let accept = accept_states(&token.dfa);
        buffer.push_str("    crate::tokens::types::TokenDfaSpec {\n");
        buffer.push_str(&format!("        regex_index: {},\n", index));
        buffer.push_str("        dfa: crate::tokens::types::SerializedDfa {\n");
        buffer.push_str(&format!(
            "            start: {},\n            class_count: {},\n            state_count: {},\n            transitions: &[{transitions}],\n            accept: &[{accept}],\n",
            token.dfa.start,
            charclass::CLASS_COUNT,
            token.dfa.transitions.len(),
            transitions = transitions.join(", "),
            accept = accept.join(", ")
        ));
        buffer.push_str("        },\n    },\n");
    }
    buffer.push_str("]\n");
    fs::write(path, buffer)?;
    Ok(())
}

fn write_class_count(out_dir: &Path) -> Result<(), Box<dyn std::error::Error>> {
    let path = out_dir.join("class_count.rs");
    fs::write(path, format!("{}", charclass::CLASS_COUNT))?;
    Ok(())
}

fn flatten_transitions(dfa: &hopcroft::MinDfa) -> Vec<String> {
    let mut items = Vec::new();
    for row in &dfa.transitions {
        for &target in row {
            items.push(format!("{}u32", target));
        }
    }
    items
}

fn accept_states(dfa: &hopcroft::MinDfa) -> Vec<String> {
    dfa.accept
        .iter()
        .map(|entry| {
            if entry.is_some() {
                "1u8".to_string()
            } else {
                "0u8".to_string()
            }
        })
        .collect()
}

fn print_summary(built: &[BuiltToken], diagrams_path: &Path) {
    println!("cargo:warning=Token minimization stats:");
    for token in built {
        let before = token.stats.dfa_states as f64;
        let after = token.stats.minimized_states as f64;
        let reduction = if before > 0.0 {
            100.0 * (1.0 - after / before)
        } else {
            0.0
        };
        println!(
            "cargo:warning=  {:<18} DFA {:>4} -> {:>4} ({:.1}% redução)",
            token.name, token.stats.dfa_states, token.stats.minimized_states, reduction
        );
    }
    println!("cargo:warning=Diagramas: {}", diagrams_path.display());
}
