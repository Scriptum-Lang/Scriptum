use std::collections::HashSet;

use pretty_assertions::assert_eq;
use proptest::prelude::*;
use scriptum_ast::{
    Module, NodeId, NodeIdGenerator, Statement, StatementKind, StringInterner, Visitor
};

proptest! {
    #[test]
    fn node_ids_sao_unicos(count in 1u32..512) {
        let mut gen = NodeIdGenerator::new();
        let mut vistos = HashSet::new();
        for _ in 0..count {
            let id = gen.fresh();
            prop_assert!(vistos.insert(id));
        }
    }
}

#[test]
fn interner_resolve_strings() {
    let mut interner = StringInterner::new();
    let a = interner.intern("salve");
    let b = interner.intern("salve");
    assert_eq!(a, b);
    assert_eq!(interner.resolve(a), "salve");
}

struct Counter {
    itens: usize,
    statements: usize,
    returns: usize,
}

impl Visitor for Counter {
    fn visit_module(&mut self, module: &Module) {
        self.itens += module.items.len();
        Visitor::visit_module(self, module);
    }

    fn visit_statement(&mut self, stmt: &Statement) {
        self.statements += 1;
        if matches!(stmt.kind, StatementKind::Return(_)) {
            self.returns += 1;
        }
        Visitor::visit_statement(self, stmt);
    }
}

#[test]
fn visitor_contabiliza_blocos() {
    let source = "functio main() { mutabilis numerus x = 1; si verum { redde x; } aliter { redde 0; } }";
    let parsed = scriptum_parser::parse_module(source).expect("parse");
    assert!(parsed.diagnostics.is_empty(), "diagnósticos inesperados: {:?}", parsed.diagnostics);
    let mut counter = Counter { itens: 0, statements: 0, returns: 0 };
    counter.visit_module(&parsed.module);
    assert_eq!(counter.itens, 1);
    assert!(counter.statements >= 4);
    assert_eq!(counter.returns, 2);
}
