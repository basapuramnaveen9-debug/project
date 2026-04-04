# Changelog

All notable changes to this project are documented here.

## v1.0.0 - 2026-04-04

### Added

- AI Optimization Lab with dedicated variant generation workflow
- Multi-language execution support for JavaScript, TypeScript, Go, Rust, C#, PHP, Ruby, and Kotlin
- Interactive execution session handling with stdin/stdout polling
- Language normalization and runtime resolution helpers
- `.env.example` for easier local setup
- VS Code launch configuration for local Flask debugging

### Improved

- Main dashboard layout and styling
- Metrics cards and result panels for a cleaner, more compact UI
- Optimized output panel so it visually matches the execution output panel
- Runtime discovery on Windows by checking common install locations for Node, Rust, .NET, PHP, and Ruby
- Automatic cached runtime/toolchain support for Deno, Go, and Kotlin
- Documentation for setup, deployment, and environment configuration

### Notes

- Runtime bootstrap artifacts are stored under `.runtime_cache`
- Local scratch execution artifacts remain excluded from Git
