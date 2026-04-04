import glob
import re
import os
import json
import platform
import shutil
import subprocess
import sys
import tarfile
import urllib.error
import urllib.request
import zipfile
import zlib
from pathlib import Path

from core.languages import normalize_language

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_CACHE_ROOT = PROJECT_ROOT / ".runtime_cache"
DENO_RELEASE_BASE_URL = "https://github.com/denoland/deno/releases/latest/download"
KOTLIN_RELEASE_API_URL = "https://api.github.com/repos/JetBrains/kotlin/releases/latest"
GO_DOWNLOAD_API_URL = "https://go.dev/dl/?mode=json&include=all"
RUNTIME_DOWNLOAD_TIMEOUT_SECONDS = 90
AUTO_INSTALL_DENO = os.getenv("STUDIO_AUTO_INSTALL_DENO", "true").strip().lower() not in {"0", "false", "no"}
AUTO_INSTALL_KOTLIN = os.getenv("STUDIO_AUTO_INSTALL_KOTLIN", "true").strip().lower() not in {"0", "false", "no"}
AUTO_INSTALL_GO = os.getenv("STUDIO_AUTO_INSTALL_GO", "true").strip().lower() not in {"0", "false", "no"}


def create_execution_artifacts(code, language, workspace, timeout_seconds=5, interactive=False):
    language = normalize_language(language)
    source_code = prepare_source_code(code, language, interactive=interactive)

    if language == "python":
        source_path = workspace / "program.py"
        source_path.write_text(source_code, encoding="utf-8")
        return {
            "ok": True,
            "run_cmd": _resolve_python_command() + [str(source_path)],
            "cwd": str(workspace),
        }

    if language == "javascript":
        run_cmd, error = _resolve_javascript_run_command()
        if error:
            return {"ok": False, "error": error}

        source_path = workspace / "program.js"
        source_path.write_text(source_code, encoding="utf-8")
        return {
            "ok": True,
            "run_cmd": run_cmd + [str(source_path)],
            "cwd": str(workspace),
        }

    if language == "typescript":
        run_cmd, error = _resolve_typescript_run_command(workspace)
        if error:
            return {"ok": False, "error": error}

        source_path = workspace / "program.ts"
        source_path.write_text(source_code, encoding="utf-8")
        return {
            "ok": True,
            "run_cmd": run_cmd + [str(source_path)],
            "cwd": str(workspace),
        }

    if language == "java":
        compiler = shutil.which("javac")
        runtime = shutil.which("java")
        if not compiler or not runtime:
            return {"ok": False, "error": "Java compiler/runtime not found. Install javac and java to run Java output."}

        class_name = _detect_java_class_name(source_code)
        source_path = workspace / f"{class_name}.java"
        source_path.write_text(source_code, encoding="utf-8")

        compile_result = _compile([compiler, str(source_path)], timeout_seconds)
        if not compile_result["ok"]:
            return compile_result

        return {
            "ok": True,
            "run_cmd": [runtime, "-cp", str(workspace), class_name],
            "cwd": str(workspace),
        }

    if language == "go":
        runtime, go_env, error = _resolve_go_command()
        if not runtime:
            return {"ok": False, "error": error or "Go toolchain not found. Install Go to run Go output."}

        source_path = workspace / "program.go"
        source_path.write_text(source_code, encoding="utf-8")
        return {
            "ok": True,
            "run_cmd": [runtime, "run", str(source_path)],
            "cwd": str(workspace),
            "env": go_env,
        }

    if language == "rust":
        compiler = _resolve_rustc_command()
        if not compiler:
            return {"ok": False, "error": "Rust compiler not found. Install rustc to run Rust output."}

        source_path = workspace / "program.rs"
        binary_path = workspace / ("program.exe" if compiler.endswith(".exe") else "program")
        source_path.write_text(source_code, encoding="utf-8")

        compile_result = _compile([compiler, str(source_path), "-o", str(binary_path)], timeout_seconds)
        if not compile_result["ok"]:
            return compile_result

        return {
            "ok": True,
            "run_cmd": [str(binary_path)],
            "cwd": str(workspace),
        }

    if language == "csharp":
        compiler = shutil.which("csc")
        if compiler:
            source_path = workspace / "Program.cs"
            binary_path = workspace / ("program.exe" if compiler.endswith(".exe") else "program")
            source_path.write_text(source_code, encoding="utf-8")

            compile_result = _compile([compiler, "/nologo", f"/out:{binary_path}", str(source_path)], timeout_seconds)
            if not compile_result["ok"]:
                return compile_result

            run_cmd = [str(binary_path)]
            if not str(binary_path).lower().endswith(".exe") and sys.platform != "win32":
                mono = shutil.which("mono")
                if mono:
                    run_cmd = [mono, str(binary_path)]

            return {
                "ok": True,
                "run_cmd": run_cmd,
                "cwd": str(workspace),
            }

        dotnet = _resolve_dotnet_command()
        if not dotnet:
            return {"ok": False, "error": "C# runtime not found. Install .NET SDK or csc to run C# output."}

        source_path = workspace / "Program.cs"
        project_path = workspace / "Studio.csproj"
        output_dir = workspace / "out"
        source_path.write_text(source_code, encoding="utf-8")
        project_path.write_text(
            """<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>disable</Nullable>
  </PropertyGroup>
</Project>
""",
            encoding="utf-8",
        )

        compile_result = _compile(
            [dotnet, "build", str(project_path), "-nologo", "-clp:ErrorsOnly", "-o", str(output_dir)],
            timeout_seconds,
        )
        if not compile_result["ok"]:
            return compile_result

        return {
            "ok": True,
            "run_cmd": [dotnet, str(output_dir / "Studio.dll")],
            "cwd": str(workspace),
        }

    if language == "php":
        runtime = _resolve_php_command()
        if not runtime:
            return {"ok": False, "error": "PHP runtime not found. Install PHP to run PHP output."}

        source_path = workspace / "program.php"
        source_path.write_text(source_code, encoding="utf-8")
        return {
            "ok": True,
            "run_cmd": [runtime, str(source_path)],
            "cwd": str(workspace),
        }

    if language == "ruby":
        runtime = _resolve_ruby_command()
        if not runtime:
            return {"ok": False, "error": "Ruby runtime not found. Install Ruby to run Ruby output."}

        source_path = workspace / "program.rb"
        source_path.write_text(source_code, encoding="utf-8")
        return {
            "ok": True,
            "run_cmd": [runtime, str(source_path)],
            "cwd": str(workspace),
        }

    if language == "kotlin":
        compiler, error = _resolve_kotlin_compiler()
        runtime = shutil.which("java")
        if not runtime:
            return {"ok": False, "error": "Java runtime not found. Install java to run Kotlin output."}
        if not compiler:
            return {"ok": False, "error": error or "Kotlin compiler not found. Install kotlinc to run Kotlin output."}

        source_path = workspace / "Main.kt"
        jar_path = workspace / "program.jar"
        source_path.write_text(source_code, encoding="utf-8")

        compile_result = _compile(_kotlin_compile_command(compiler, source_path, jar_path), timeout_seconds)
        if not compile_result["ok"]:
            return compile_result

        return {
            "ok": True,
            "run_cmd": [runtime, "-jar", str(jar_path)],
            "cwd": str(workspace),
        }

    if language == "cpp":
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            return {"ok": False, "error": "C++ compiler not found. Install g++ or clang++ to run C++ output."}

        source_path = workspace / "program.cpp"
        binary_path = workspace / ("program.exe" if compiler.endswith(".exe") else "program")
        source_path.write_text(source_code, encoding="utf-8")

        compile_result = _compile([compiler, str(source_path), "-o", str(binary_path)], timeout_seconds)
        if not compile_result["ok"]:
            return compile_result

        return {
            "ok": True,
            "run_cmd": [str(binary_path)],
            "cwd": str(workspace),
        }

    compiler = shutil.which("gcc") or shutil.which("clang")
    if not compiler:
        return {"ok": False, "error": "C compiler not found. Install gcc or clang to run C output."}

    source_path = workspace / "program.c"
    binary_path = workspace / ("program.exe" if compiler.endswith(".exe") else "program")
    source_path.write_text(source_code, encoding="utf-8")

    compile_result = _compile([compiler, str(source_path), "-o", str(binary_path)], timeout_seconds)
    if not compile_result["ok"]:
        return compile_result

    return {
        "ok": True,
        "run_cmd": [str(binary_path)],
        "cwd": str(workspace),
    }


def prepare_source_code(code, language, interactive=False):
    language = normalize_language(language)
    if not interactive:
        return code

    if language == "c":
        main_match = re.search(r"\bint\s+main\s*\([^)]*\)\s*\{", code)
        if not main_match:
            return code
        insertion = "\n    setvbuf(stdout, NULL, _IONBF, 0);\n"
        return code[: main_match.end()] + insertion + code[main_match.end() :]

    if language == "cpp" and "std::cout" in code:
        main_match = re.search(r"\bint\s+main\s*\([^)]*\)\s*\{", code)
        if not main_match:
            return code
        insertion = "\n  std::cout << std::unitbuf;\n"
        return code[: main_match.end()] + insertion + code[main_match.end() :]

    return code


def _compile(command, timeout_seconds):
    try:
        compile_result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Compilation timed out."}

    if compile_result.returncode != 0:
        error_text = (compile_result.stderr or compile_result.stdout or "").strip()
        return {"ok": False, "error": error_text or "Compilation failed with unknown error."}

    return {"ok": True}


def _detect_java_class_name(code):
    public_match = re.search(r"\bpublic\s+class\s+([A-Za-z_]\w*)\b", code)
    if public_match:
        return public_match.group(1)

    main_class_match = re.search(
        r"\bclass\s+([A-Za-z_]\w*)\b[\s\S]*?\bpublic\s+static\s+void\s+main\s*\(",
        code,
    )
    if main_class_match:
        return main_class_match.group(1)

    plain_class_match = re.search(r"\bclass\s+([A-Za-z_]\w*)\b", code)
    if plain_class_match:
        return plain_class_match.group(1)

    return "Main"


def _resolve_python_command():
    python = shutil.which("python")
    if python:
        return [python, "-u"]

    launcher = shutil.which("py")
    if launcher:
        return [launcher, "-3", "-u"]

    return [sys.executable, "-u"]


def _resolve_typescript_run_command(_workspace):
    tsx = shutil.which("tsx")
    if tsx:
        return [tsx], None

    ts_node = shutil.which("ts-node")
    if ts_node:
        return [ts_node], None

    deno = shutil.which("deno")
    if deno:
        return _deno_run_command(deno), None

    bun = shutil.which("bun")
    if bun:
        return [bun], None

    deno, error = _resolve_deno_command()
    if deno:
        return _deno_run_command(deno), None

    return None, error or (
        "TypeScript runtime not found. Install tsx, ts-node, deno, or bun to run TypeScript output."
    )


def _resolve_javascript_run_command():
    node = _resolve_node_command()
    if node:
        return [node], None

    deno, error = _resolve_deno_command()
    if deno:
        return _deno_run_command(deno), None

    return None, error or "JavaScript runtime not found. Install Node.js or Deno to run JavaScript output."


def _resolve_node_command():
    return _resolve_known_binary(
        env_var="STUDIO_NODE_PATH",
        command="node",
        patterns=[
            r"C:\Program Files\nodejs\node.exe",
            r"C:\Program Files (x86)\nodejs\node.exe",
            str(Path.home() / "AppData/Local/Programs/nodejs/node.exe"),
        ],
    )


def _resolve_rustc_command():
    return _resolve_known_binary(
        env_var="STUDIO_RUSTC_PATH",
        command="rustc",
        patterns=[
            str(Path.home() / ".cargo/bin/rustc.exe"),
            str(Path.home() / ".cargo/bin/rustc"),
        ],
    )


def _resolve_dotnet_command():
    return _resolve_known_binary(
        env_var="STUDIO_DOTNET_PATH",
        command="dotnet",
        patterns=[
            r"C:\Program Files\dotnet\dotnet.exe",
            r"C:\Program Files (x86)\dotnet\dotnet.exe",
        ],
    )


def _resolve_php_command():
    local_packages = Path.home() / "AppData/Local/Microsoft/WinGet/Packages"
    return _resolve_known_binary(
        env_var="STUDIO_PHP_PATH",
        command="php",
        patterns=[
            r"C:\Program Files\PHP\php.exe",
            r"C:\Program Files\PHP\*\php.exe",
            str(local_packages / "PHP.PHP.*_Microsoft.Winget.Source_8wekyb3d8bbwe/php.exe"),
            str(Path.home() / "AppData/Local/Programs/PHP/php.exe"),
        ],
    )


def _resolve_ruby_command():
    return _resolve_known_binary(
        env_var="STUDIO_RUBY_PATH",
        command="ruby",
        patterns=[
            r"C:\Ruby*\bin\ruby.exe",
            str(Path.home() / "AppData/Local/Programs/Ruby/*/bin/ruby.exe"),
        ],
    )


def _resolve_known_binary(env_var, command, patterns):
    configured_path = os.getenv(env_var)
    if configured_path:
        configured = Path(configured_path).expanduser()
        if configured.exists():
            return str(configured)

    resolved = shutil.which(command)
    if resolved:
        return resolved

    for pattern in patterns:
        for candidate in sorted(glob.glob(os.path.expandvars(os.path.expanduser(str(pattern))))):
            if Path(candidate).exists():
                return candidate

    return None


def _resolve_go_command():
    configured_path = os.getenv("STUDIO_GO_PATH")
    if configured_path:
        configured = _resolve_go_binary_path(configured_path)
        if configured:
            return configured, _go_runtime_env(configured), None

    go_binary = shutil.which("go")
    if go_binary:
        return go_binary, _go_runtime_env(go_binary), None

    bundled = _bundled_go_path()
    if bundled.exists():
        return str(bundled), _go_runtime_env(bundled), None

    if not AUTO_INSTALL_GO:
        return None, None, "Go toolchain not found. Set STUDIO_GO_PATH or install Go."

    installed, error = _install_bundled_go()
    if installed:
        return installed, _go_runtime_env(installed), None

    return None, None, error or "Go toolchain not found. Install Go to run Go output."


def _resolve_deno_command():
    configured_path = os.getenv("STUDIO_DENO_PATH")
    if configured_path:
        configured = Path(configured_path).expanduser()
        if configured.exists():
            return str(configured), None

    deno = shutil.which("deno")
    if deno:
        return deno, None

    bundled_path = _bundled_deno_path()
    if bundled_path.exists():
        return str(bundled_path), None

    if not AUTO_INSTALL_DENO:
        return None, "Deno runtime not found. Set STUDIO_DENO_PATH or install Deno."

    return _install_bundled_deno()


def _resolve_go_binary_path(path_value):
    candidate = Path(path_value).expanduser()
    if candidate.is_dir():
        nested = candidate / ("bin/go.exe" if os.name == "nt" else "bin/go")
        if nested.exists():
            return str(nested)

    if candidate.exists():
        return str(candidate)

    return None


def _go_runtime_env(go_binary):
    cache_root = RUNTIME_CACHE_ROOT / "go"
    build_cache = cache_root / "build-cache"
    gopath = cache_root / "gopath"
    goenv = cache_root / "env"

    for path in (build_cache, gopath, gopath / "pkg" / "mod"):
        path.mkdir(parents=True, exist_ok=True)

    env = {
        "GOCACHE": str(build_cache),
        "GOPATH": str(gopath),
        "GOMODCACHE": str(gopath / "pkg" / "mod"),
        "GOENV": str(goenv),
    }

    goroot = _go_root_from_binary(go_binary)
    if goroot:
        env["GOROOT"] = goroot

    return env


def _go_root_from_binary(go_binary):
    try:
        binary_path = Path(go_binary).resolve()
    except OSError:
        return None

    parent = binary_path.parent
    if parent.name.lower() != "bin":
        return None

    goroot = parent.parent
    if (goroot / "src").exists():
        return str(goroot)

    return None


def _install_bundled_go():
    cache_dir = RUNTIME_CACHE_ROOT / "go"
    extract_dir = cache_dir / "dist"
    temp_extract_dir = cache_dir / "dist.download"
    temp_archive_path = cache_dir / "go.archive.download"

    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        existing = _bundled_go_path()
        if existing.exists():
            return str(existing), None

        release, asset, error = _fetch_go_release_asset()
        if not asset:
            return None, error or "Could not find a compatible Go archive for this platform."

        filename = asset.get("filename") or "go.archive"
        temp_archive_path = cache_dir / f"{filename}.download"

        _cleanup_go_install_temp_paths(temp_archive_path, temp_extract_dir)

        request = urllib.request.Request(
            asset["url"],
            headers={"User-Agent": "OptimizationStudio/1.0"},
        )
        with urllib.request.urlopen(request, timeout=RUNTIME_DOWNLOAD_TIMEOUT_SECONDS) as response:
            with open(temp_archive_path, "wb") as archive_file:
                shutil.copyfileobj(response, archive_file)

        if filename.endswith(".zip"):
            with zipfile.ZipFile(temp_archive_path) as archive:
                archive.extractall(temp_extract_dir)
        elif filename.endswith(".tar.gz"):
            with tarfile.open(temp_archive_path, "r:gz") as archive:
                archive.extractall(temp_extract_dir)
        else:
            return None, f"Unsupported Go archive format for {filename}."

        compiler_path = _bundled_go_path(root=temp_extract_dir)
        if not compiler_path.exists():
            return None, (
                f"Downloaded Go archive for {release.get('version', 'the selected release')} "
                "did not contain the expected go executable."
            )

        if os.name != "nt":
            compiler_path.chmod(0o755)

        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        shutil.move(str(temp_extract_dir), str(extract_dir))

        return str(_bundled_go_path()), None
    except urllib.error.URLError as exc:
        return None, (
            "Go toolchain was not installed locally, and automatic download failed. "
            f"Install Go manually or set STUDIO_GO_PATH. Details: {exc}"
        )
    except (OSError, zipfile.BadZipFile, tarfile.TarError, zlib.error, ValueError) as exc:
        return None, (
            "Bundled Go setup failed while preparing the runtime cache. "
            f"Install Go manually or set STUDIO_GO_PATH. Details: {exc}"
        )
    finally:
        _cleanup_go_install_temp_paths(temp_archive_path, temp_extract_dir)


def _fetch_go_release_asset():
    normalized_os, normalized_arch, error = _go_platform_key()
    if error:
        return None, None, error

    request = urllib.request.Request(
        GO_DOWNLOAD_API_URL,
        headers={
            "User-Agent": "OptimizationStudio/1.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=RUNTIME_DOWNLOAD_TIMEOUT_SECONDS) as response:
        releases = json.loads(response.read().decode("utf-8"))

    stable_releases = [release for release in releases if release.get("stable")]
    ordered_releases = stable_releases or releases

    for release in ordered_releases:
        for asset in release.get("files", []):
            if asset.get("kind") != "archive":
                continue
            if asset.get("os") != normalized_os or asset.get("arch") != normalized_arch:
                continue
            return release, {
                "filename": asset.get("filename"),
                "url": f"https://go.dev/dl/{asset.get('filename')}",
            }, None

    return None, None, (
        "Automatic Go setup is not available for "
        f"platform '{normalized_os}' and architecture '{normalized_arch}'."
    )


def _go_platform_key():
    system = platform.system().lower()
    machine = platform.machine().lower()

    normalized_system = {
        "windows": "windows",
        "linux": "linux",
        "darwin": "darwin",
    }.get(system)

    normalized_arch = {
        "amd64": "amd64",
        "x64": "amd64",
        "x86_64": "amd64",
        "arm64": "arm64",
        "aarch64": "arm64",
    }.get(machine)

    if not normalized_system:
        return None, None, f"Automatic Go setup is not available for platform '{system}'."

    if not normalized_arch:
        return None, None, f"Automatic Go setup is not available for architecture '{machine}'."

    return normalized_system, normalized_arch, None


def _cleanup_go_install_temp_paths(temp_archive_path, temp_extract_dir):
    try:
        Path(temp_archive_path).unlink()
    except OSError:
        pass

    if Path(temp_extract_dir).exists():
        shutil.rmtree(temp_extract_dir, ignore_errors=True)


def _bundled_go_path(root=None):
    base = Path(root) if root else (RUNTIME_CACHE_ROOT / "go" / "dist")
    relative = Path("go/bin/go.exe" if os.name == "nt" else "go/bin/go")
    return base / relative


def _install_bundled_deno():
    asset_name, error = _deno_asset_name()
    if error:
        return None, error

    cache_dir = RUNTIME_CACHE_ROOT / "deno"
    executable_path = _bundled_deno_path()
    archive_path = cache_dir / asset_name
    temp_archive_path = cache_dir / f"{asset_name}.download"
    temp_executable_path = cache_dir / f"{executable_path.name}.download"

    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        if executable_path.exists():
            return str(executable_path), None

        request = urllib.request.Request(
            f"{DENO_RELEASE_BASE_URL}/{asset_name}",
            headers={"User-Agent": "OptimizationStudio/1.0"},
        )
        with urllib.request.urlopen(request, timeout=RUNTIME_DOWNLOAD_TIMEOUT_SECONDS) as response:
            with open(temp_archive_path, "wb") as archive_file:
                shutil.copyfileobj(response, archive_file)

        with zipfile.ZipFile(temp_archive_path) as archive:
            member_name = next((name for name in archive.namelist() if name.endswith(_bundled_deno_path().name)), None)
            if not member_name:
                return None, "Downloaded Deno archive did not contain the runtime executable."

            with archive.open(member_name) as source_file, open(temp_executable_path, "wb") as target_file:
                shutil.copyfileobj(source_file, target_file)

        if os.name != "nt":
            temp_executable_path.chmod(0o755)

        temp_executable_path.replace(executable_path)
        return str(executable_path), None
    except urllib.error.URLError as exc:
        return None, (
            "Deno runtime was not installed locally, and automatic Deno download failed. "
            f"Install Deno manually or set STUDIO_DENO_PATH. Details: {exc}"
        )
    except (OSError, zipfile.BadZipFile) as exc:
        return None, (
            "Bundled Deno setup failed while preparing the runtime cache. "
            f"Install Deno manually or set STUDIO_DENO_PATH. Details: {exc}"
        )
    finally:
        for temp_path in (temp_archive_path, temp_executable_path):
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass


def _bundled_deno_path():
    executable_name = "deno.exe" if os.name == "nt" else "deno"
    return RUNTIME_CACHE_ROOT / "deno" / executable_name


def _deno_asset_name():
    system = platform.system().lower()
    machine = platform.machine().lower()

    normalized_machine = {
        "amd64": "x86_64",
        "x64": "x86_64",
        "x86_64": "x86_64",
        "arm64": "aarch64",
        "aarch64": "aarch64",
    }.get(machine)

    if not normalized_machine:
        return None, f"Automatic Deno setup is not available for architecture '{machine}'."

    if system == "windows":
        return f"deno-{normalized_machine}-pc-windows-msvc.zip", None

    if system == "linux":
        return f"deno-{normalized_machine}-unknown-linux-gnu.zip", None

    if system == "darwin":
        return f"deno-{normalized_machine}-apple-darwin.zip", None

    return None, f"Automatic Deno setup is not available for platform '{system}'."


def _deno_run_command(deno_path):
    return [str(deno_path), "run", "--quiet", "--unstable-detect-cjs"]


def _resolve_kotlin_compiler():
    configured_path = os.getenv("STUDIO_KOTLINC_PATH")
    if configured_path:
        configured = Path(configured_path).expanduser()
        if configured.exists():
            return str(configured), None

    compiler = shutil.which("kotlinc")
    if compiler:
        return compiler, None

    bundled = _bundled_kotlinc_path()
    if bundled.exists():
        return str(bundled), None

    if not AUTO_INSTALL_KOTLIN:
        return None, "Kotlin compiler not found. Set STUDIO_KOTLINC_PATH or install kotlinc."

    return _install_bundled_kotlin_compiler()


def _install_bundled_kotlin_compiler():
    cache_dir = RUNTIME_CACHE_ROOT / "kotlin"
    zip_path = cache_dir / "kotlin-compiler.zip"
    extract_dir = cache_dir / "dist"
    temp_zip_path = cache_dir / "kotlin-compiler.zip.download"
    temp_extract_dir = cache_dir / "dist.download"
    compiler_path = _bundled_kotlinc_path(root=temp_extract_dir)

    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        existing = _bundled_kotlinc_path()
        if existing.exists():
            return str(existing), None

        release = _fetch_latest_kotlin_release()
        asset = next(
            (item for item in release.get("assets", []) if str(item.get("name", "")).startswith("kotlin-compiler-") and str(item.get("name", "")).endswith(".zip")),
            None,
        )
        if not asset or not asset.get("browser_download_url"):
            return None, "Could not find the Kotlin compiler zip in the official Kotlin release assets."

        last_error = None
        for _attempt in range(2):
            _cleanup_kotlin_install_temp_paths(temp_zip_path, temp_extract_dir)

            try:
                request = urllib.request.Request(
                    asset["browser_download_url"],
                    headers={
                        "User-Agent": "OptimizationStudio/1.0",
                        "Accept": "application/octet-stream",
                    },
                )
                with urllib.request.urlopen(request, timeout=RUNTIME_DOWNLOAD_TIMEOUT_SECONDS) as response:
                    with open(temp_zip_path, "wb") as archive_file:
                        shutil.copyfileobj(response, archive_file)

                with zipfile.ZipFile(temp_zip_path) as archive:
                    archive.extractall(temp_extract_dir)

                if not compiler_path.exists():
                    return None, "Downloaded Kotlin compiler archive did not contain the expected kotlinc executable."

                if os.name != "nt":
                    compiler_path.chmod(0o755)

                if extract_dir.exists():
                    shutil.rmtree(extract_dir)
                shutil.move(str(temp_extract_dir), str(extract_dir))
                temp_zip_path.replace(zip_path)
                return str(_bundled_kotlinc_path()), None
            except (urllib.error.URLError, OSError, zipfile.BadZipFile, zlib.error, ValueError) as exc:
                last_error = exc

        if isinstance(last_error, urllib.error.URLError):
            return None, (
                "Kotlin compiler was not installed locally, and automatic download failed. "
                f"Install kotlinc manually or set STUDIO_KOTLINC_PATH. Details: {last_error}"
            )

        return None, (
            "Bundled Kotlin compiler setup failed while preparing the runtime cache. "
            f"Install kotlinc manually or set STUDIO_KOTLINC_PATH. Details: {last_error}"
        )
    except urllib.error.URLError as exc:
        return None, (
            "Kotlin compiler was not installed locally, and automatic download failed. "
            f"Install kotlinc manually or set STUDIO_KOTLINC_PATH. Details: {exc}"
        )
    except (OSError, zipfile.BadZipFile, zlib.error, ValueError) as exc:
        return None, (
            "Bundled Kotlin compiler setup failed while preparing the runtime cache. "
            f"Install kotlinc manually or set STUDIO_KOTLINC_PATH. Details: {exc}"
        )
    finally:
        _cleanup_kotlin_install_temp_paths(temp_zip_path, temp_extract_dir)


def _fetch_latest_kotlin_release():
    request = urllib.request.Request(
        KOTLIN_RELEASE_API_URL,
        headers={
            "User-Agent": "OptimizationStudio/1.0",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(request, timeout=RUNTIME_DOWNLOAD_TIMEOUT_SECONDS) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)


def _cleanup_kotlin_install_temp_paths(temp_zip_path, temp_extract_dir):
    try:
        temp_zip_path.unlink()
    except OSError:
        pass
    if temp_extract_dir.exists():
        shutil.rmtree(temp_extract_dir, ignore_errors=True)


def _bundled_kotlinc_path(root=None):
    base = Path(root) if root else (RUNTIME_CACHE_ROOT / "kotlin" / "dist")
    relative = Path("kotlinc/bin/kotlinc.bat" if os.name == "nt" else "kotlinc/bin/kotlinc")
    return base / relative


def _kotlin_compile_command(compiler_path, source_path, jar_path):
    compiler = str(compiler_path)
    args = [compiler, str(source_path), "-include-runtime", "-d", str(jar_path)]
    if os.name == "nt" and compiler.lower().endswith((".bat", ".cmd")):
        return ["cmd.exe", "/d", "/c", *args]
    return args
