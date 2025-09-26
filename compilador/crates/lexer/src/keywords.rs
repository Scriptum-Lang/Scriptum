use crate::tokens::{KeywordKind, TokenKind};

/// Retorna o token de palavra-chave associado ao lexema.
pub fn lookup_keyword(ident: &str) -> Option<TokenKind> {
    let keyword = match ident {
        "definire" => KeywordKind::Definire,
        "finis" => KeywordKind::Finis,
        "si" => KeywordKind::Si,
        "alioqui" => KeywordKind::Alioqui,
        "dum" => KeywordKind::Dum,
        "verum" => KeywordKind::Verum,
        "falsum" => KeywordKind::Falsum,
        "reditus" => KeywordKind::Reditus,
        _ => return None,
    };
    Some(TokenKind::Keyword(keyword))
}
