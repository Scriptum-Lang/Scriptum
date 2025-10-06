use std::path::{Path, PathBuf};

pub fn manifest_path(relative: &str) -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join(relative)
}

pub fn snapshot_name(base: &Path, path: &Path) -> String {
    path
        .strip_prefix(base)
        .unwrap()
        .with_extension("")
        .to_string_lossy()
        .replace('\\', "__")
        .replace('/', "__")
}
