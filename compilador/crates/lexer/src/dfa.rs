use memchr::memchr;

/// Avança até o final de um identificador.
pub fn identifier_end(input: &str) -> usize {
    let mut len = 0;
    for ch in input.chars() {
        if ch == '_' || ch.is_ascii_alphanumeric() {
            len += ch.len_utf8();
        } else {
            break;
        }
    }
    len
}

/// Avança até o final de um literal numérico simples.
pub fn number_end(input: &str) -> usize {
    let mut len = 0;
    let mut seen_dot = false;
    for ch in input.chars() {
        if ch == '.' {
            if seen_dot {
                break;
            }
            seen_dot = true;
            len += 1;
        } else if ch.is_ascii_digit() {
            len += 1;
        } else {
            break;
        }
    }
    len
}

/// Ignora espaços e comentários retornando o novo offset relativo.
pub fn skip_ignorable(input: &str) -> usize {
    let bytes = input.as_bytes();
    let mut idx = 0;
    while idx < bytes.len() {
        match bytes[idx] {
            b' ' | b'\r' | b'\t' | b'\n' => idx += 1,
            b'/' if bytes.get(idx + 1) == Some(&b'/') => {
                let rest = &input[idx + 2..];
                if let Some(pos) = memchr(b'\n', rest.as_bytes()) {
                    idx += 2 + pos + 1;
                } else {
                    return bytes.len();
                }
            }
            b'/' if bytes.get(idx + 1) == Some(&b'*') => {
                idx += 2;
                while idx + 1 < bytes.len() {
                    if bytes[idx] == b'*' && bytes[idx + 1] == b'/' {
                        idx += 2;
                        break;
                    }
                    idx += 1;
                }
            }
            _ => break,
        }
    }
    idx.min(bytes.len())
}
