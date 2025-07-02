<h1>
  <img src="./doc/fourmind-logo.png" alt="Logo" width="30"> 
  FourMind
</h1>

[Report](doc/report.pdf)

An implementation of a LLM-powered Bot designed for the [TuringGame](https://www.turinggame.ai/). This implementation is based on the [TuringBotClient](https://github.com/SCCH-Nessler/TuringBotClient) library.


## 🚀 Getting Started

Follow these steps to set up the project and start using it:

### **⚡ Install `uv` and Dependencies**

This project uses **`uv`** for dependency management. You can install `uv` by following the official documentation: [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/).

To install `uv`, run:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Once `uv` is installed, sync all dependencies:

```bash
uv sync --all-extras
```

This ensures all required dependencies, including optional extras, are installed for the environment.

Additionally, this project uses **pre-commit** to enforce code formatting and quality checks before committing changes. Set up the pre-commit hooks by running:

```bash
uv run pre-commit install
```

To manually check all files using pre-commit, run:

```bash
uv run pre-commit run --all-files
```

### **🔧 Configure Environment Variables**

This project requires a `.env` file for configuration.

1. Copy the `.env.example` template and create your own `.env` file:
   ```bash
   cp .env.example .env
   ```
2. Update the `.env` file with your actual secrets and credentials.
3. Ensure `.env` is **never committed to Git** (it is already included in `.gitignore`).

The `.env` file is used by both **Docker Compose** and **FourMind** for configuration.

---

### **🐳 Build and Run the Docker Container**

1. Build the Docker container using the provided `docker-compose.yml` file:
   ```bash
   docker compose up -d --build
   ```


### **🛠️ Run the Bot**

1. If no docker is available, start the bot using the following command:
   ```bash
   uv run fourmind
   ```
