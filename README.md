# envault

> CLI tool to manage and encrypt per-project `.env` files with git-friendly diffs

---

## Installation

```bash
pip install envault
```

Or with [pipx](https://pypa.github.io/pipx/) (recommended):

```bash
pipx install envault
```

---

## Usage

Initialize envault in your project:

```bash
envault init
```

Add and encrypt your `.env` file:

```bash
envault lock .env
```

Decrypt and load secrets for your current session:

```bash
envault unlock .env
```

View a clean, git-friendly diff of changes between versions:

```bash
envault diff .env
```

Secrets are stored encrypted in `.env.vault`, which is safe to commit. Add `.env` to your `.gitignore` and track `.env.vault` instead.

```bash
echo ".env" >> .gitignore
git add .env.vault
```

---

## How It Works

- Encrypts `.env` files using AES-256, keyed from a local secret or environment variable
- Produces line-level diffs on the encrypted vault file so changes remain reviewable in pull requests
- Per-project key isolation ensures secrets never leak across repositories

---

## License

MIT © [envault contributors](https://github.com/yourname/envault)