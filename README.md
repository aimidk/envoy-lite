# envoy-lite

> Lightweight environment variable manager with secret injection for local dev workflows

---

## Installation

```bash
pip install envoy-lite
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv add envoy-lite
```

---

## Usage

Create a `.env.yaml` file in your project root:

```yaml
APP_ENV: development
DATABASE_URL: postgres://localhost:5432/mydb
API_KEY: !secret vault:myapp/api_key
```

Then load and inject variables into your environment:

```python
import envoy_lite

envoy_lite.load(".env.yaml")

import os
print(os.getenv("APP_ENV"))      # "development"
print(os.getenv("API_KEY"))      # resolved secret value
```

Or use the CLI to run a process with injected variables:

```bash
envoy run --env .env.yaml -- python app.py
```

Secrets are resolved at runtime from your configured backend (e.g., HashiCorp Vault, AWS Secrets Manager) and are never written to disk.

---

## Features

- 📄 YAML-based environment configuration
- 🔐 Secret injection from popular secret backends
- ⚡ Zero-config defaults for local development
- 🧩 Simple Python API and CLI interface

---

## License

MIT © [envoy-lite contributors](https://github.com/your-org/envoy-lite)