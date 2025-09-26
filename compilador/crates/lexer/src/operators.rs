use crate::tokens::OperatorKind;

/// Mapeia lexemas para operadores conhecidos.
pub fn match_operator(input: &str) -> Option<OperatorKind> {
    match input {
        "=" => Some(OperatorKind::Assign),
        "+" => Some(OperatorKind::Plus),
        "-" => Some(OperatorKind::Minus),
        "*" => Some(OperatorKind::Star),
        "/" => Some(OperatorKind::Slash),
        "==" => Some(OperatorKind::Eq),
        "!=" => Some(OperatorKind::Ne),
        "<" => Some(OperatorKind::Lt),
        "<=" => Some(OperatorKind::Le),
        ">" => Some(OperatorKind::Gt),
        ">=" => Some(OperatorKind::Ge),
        _ => None,
    }
}
