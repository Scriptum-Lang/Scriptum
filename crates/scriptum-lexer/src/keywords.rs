use std::collections::HashMap;

use once_cell::sync::Lazy;

use crate::tokens::Keyword;

/// Mapa global de palavras-chave.
pub static KEYWORDS: Lazy<HashMap<&'static str, Keyword>> = Lazy::new(|| {
    use Keyword::*;
    HashMap::from([
        ("mutabilis", Mutabilis),
        ("constans", Constans),
        ("functio", Functio),
        ("structura", Structura),
        ("si", Si),
        ("aliter", Aliter),
        ("dum", Dum),
        ("pro", Pro),
        ("in", In),
        ("de", De),
        ("redde", Redde),
        ("frange", Frange),
        ("perge", Perge),
        ("verum", Verum),
        ("falsum", Falsum),
        ("nullum", Nullum),
        ("indefinitum", Indefinitum),
        ("numerus", Numerus),
        ("textus", Textus),
        ("booleanum", Booleanum),
        ("vacuum", Vacuum),
        ("quodlibet", Quodlibet),
    ])
});
