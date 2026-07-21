use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::thread;
use std::time::Duration;
use std::net::{SocketAddr, TcpStream};
use std::str::FromStr;

use tauri::path::BaseDirectory;
use tauri::{AppHandle, Emitter, Manager};

pub struct BackendProcess(pub Mutex<Option<Child>>);

// -- PER-REPO: Customize these constants --
const BACKEND_NAME: &str = "ocr-mcp-backend.exe";
const BACKEND_PORT: u16 = 10859;
const BACKEND_TAG: &str = "ocr-mcp-backend-x86_64-pc-windows-msvc.exe";
const ENV_PORT: &str = "PORT";
const ENV_HOST: &str = "HOST";
const ENV_TAURI: &str = "OCR_MCP_TAURI";

fn dev_backend_path() -> Option<PathBuf> {
    if !cfg!(debug_assertions) {
        return None;
    }
    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("binaries")
        .join(BACKEND_TAG);
    path.exists().then_some(path)
}

fn log_line(app: &AppHandle, message: &str) {
    eprintln!("[backend] {message}");
    if let Ok(dir) = app.path().app_log_dir() {
        let _ = fs::create_dir_all(&dir);
        let log_path = dir.join("backend-spawn.log");
        if let Ok(mut file) = OpenOptions::new().create(true).append(true).open(log_path) {
            let _ = writeln!(file, "{message}");
        }
    }
}

fn resolve_bundled_backend(app: &AppHandle) -> Result<PathBuf, String> {
    let mut tried = Vec::new();

    if let Ok(path) = app.path().resolve(BACKEND_NAME, BaseDirectory::Resource) {
        tried.push(path.display().to_string());
        if path.exists() {
            return Ok(path);
        }
    }

    let resources_path = format!("resources/{BACKEND_NAME}");
    if let Ok(path) = app.path().resolve(&resources_path, BaseDirectory::Resource) {
        tried.push(path.display().to_string());
        if path.exists() {
            return Ok(path);
        }
    }

    if let Ok(dir) = app.path().executable_dir() {
        let path = dir.join("resources").join(BACKEND_NAME);
        tried.push(path.display().to_string());
        if path.exists() {
            return Ok(path);
        }
    }

    Err(format!("bundled backend missing from resources (tried: {})", tried.join("; ")))
}

fn install_dir_from_backend(path: &PathBuf) -> PathBuf {
    if let Some(parent) = path.parent() {
        if parent
            .file_name()
            .is_some_and(|name| name.eq_ignore_ascii_case("resources"))
        {
            if let Some(install_dir) = parent.parent() {
                return install_dir.to_path_buf();
            }
        }
        return parent.to_path_buf();
    }
    PathBuf::from(".")
}

pub fn materialize_backend(app: &AppHandle) -> Result<PathBuf, String> {
    if let Some(dev_path) = dev_backend_path() {
        log_line(app, &format!("using dev backend: {}", dev_path.display()));
        return Ok(dev_path);
    }

    let bundled = resolve_bundled_backend(app)?;
    log_line(app, &format!("using bundled backend: {}", bundled.display()));
    Ok(bundled)
}

fn free_port(port: u16) {
    #[cfg(windows)]
    {
        let script = format!("Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | ForEach-Object {{ taskkill /F /PID `$_.OwningProcess /T 2>$null }}");
        let _ = Command::new("powershell.exe")
            .args(["-NoProfile", "-Command", &script])
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status();
        thread::sleep(Duration::from_millis(300));
    }
}

fn stop_managed_child(state: &BackendProcess) {
    if let Some(mut child) = state.0.lock().unwrap().take() {
        let _ = child.kill();
        let _ = child.wait();
    }
}

pub fn spawn_backend(app: AppHandle, state: &BackendProcess) -> Result<String, String> {
    stop_managed_child(state);
    free_port(BACKEND_PORT);

    let backend_path = materialize_backend(&app)?;
    let workdir = app
        .path()
        .executable_dir()
        .ok()
        .unwrap_or_else(|| install_dir_from_backend(&backend_path));

    log_line(
        &app,
        &format!("spawning {} (cwd {}) on port 10859",
            backend_path.display(), workdir.display()),
    );

    let mut command = Command::new(&backend_path);
    command
        .current_dir(&workdir)
        .env(ENV_PORT, BACKEND_PORT.to_string())
        .env(ENV_HOST, "127.0.0.1")
        .env(ENV_TAURI, "1")
        .stdout(Stdio::null())
        .stderr(Stdio::null());

    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NO_WINDOW: u32 = 0x0800_0000;
        command.creation_flags(CREATE_NO_WINDOW);
    }

    let mut child = command
        .spawn()
        .map_err(|e| format!("Failed to spawn {}: {e}", backend_path.display()))?;

    state.0.lock().unwrap().replace(child);

    // Poll backend TCP port to confirm it's actually listening
    let addr = SocketAddr::from_str(&format!("127.0.0.1:{BACKEND_PORT}")).unwrap();
    let app_health = app.clone();
    thread::spawn(move || {
        for attempt in 0..30 {
            thread::sleep(Duration::from_secs(2));
            match TcpStream::connect_timeout(&addr, Duration::from_secs(2)) {
                Ok(_) => {
                    log_line(&app_health, &format!("Backend health check PASSED on port {BACKEND_PORT} (attempt {})", attempt + 1));
                    let _ = app_health.emit("backend-status", "ready");
                    return;
                }
                Err(e) => {
                    log_line(&app_health, &format!("Backend health check: {e} (attempt {})", attempt + 1));
                }
            }
        }
        log_line(&app_health, &format!("Backend health check FAILED -- not listening on port {BACKEND_PORT} after 30 attempts"));
        let _ = app_health.emit("backend-status", "error: backend not reachable");
    });

    Ok(format!("Backend starting on port {BACKEND_PORT}"))
}
