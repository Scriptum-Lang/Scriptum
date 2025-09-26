use indexmap::IndexMap;
use smallvec::SmallVec;

use scriptum_ast::Symbol;
use scriptum_utils::Span;

use crate::type_system::Type;

/// Tabela de símbolos hierárquica com escopos aninhados.
pub struct SymbolTable {
    scopes: SmallVec<[IndexMap<Symbol, (Type, Span)>; 8]>,
}

impl SymbolTable {
    pub fn new() -> Self {
        let mut table = Self {
            scopes: SmallVec::new(),
        };
        table.enter_scope();
        table
    }

    pub fn enter_scope(&mut self) {
        self.scopes.push(IndexMap::new());
    }

    pub fn exit_scope(&mut self) {
        self.scopes.pop();
    }

    pub fn insert(&mut self, symbol: Symbol, ty: Type, span: Span) -> Option<(Type, Span)> {
        self.scopes
            .last_mut()
            .expect("escopo vazio")
            .insert(symbol, (ty, span))
    }

    pub fn contains_in_current(&self, symbol: Symbol) -> bool {
        self.scopes
            .last()
            .map(|scope| scope.contains_key(&symbol))
            .unwrap_or(false)
    }

    pub fn lookup(&self, symbol: Symbol) -> Option<(Type, Span)> {
        for scope in self.scopes.iter().rev() {
            if let Some(entry) = scope.get(&symbol) {
                return Some(*entry);
            }
        }
        None
    }
}
