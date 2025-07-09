# Data Extraction Using Azure Content Understanding

This project uses a Python development container for a consistent development environment across different machines.

## 🐳 Dev Container Setup

This repository includes a complete dev container configuration that provides:

- **Python 3.12** runtime environment
- **Azure CLI** for Azure resource management
- **GitHub CLI** for repository operations
- **Essential Python packages** for data processing and Azure integration
- **VS Code extensions** for Python development, linting, and formatting

### Prerequisites

- [Docker](https://www.docker.com/get-started)
- [Visual Studio Code](https://code.visualstudio.com/)
- [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

### Getting Started

1. **Clone this repository**
   ```bash
   git clone <repository-url>
   cd data-extraction-using-azure-content-understanding
   ```

2. **Open in VS Code**
   ```bash
   code .
   ```

3. **Reopen in Container**
   - VS Code will prompt you to reopen the folder in a container
   - Or use the Command Palette (Cmd+Shift+P) and select "Dev Containers: Reopen in Container"

4. **Configure Azure Credentials**
   ```bash
   cp .env.example .env
   # Edit .env with your Azure credentials
   ```

5. **Run the sample script**
   ```bash
   python main.py
   ```

## 📦 Included Packages

### Core Dependencies
- `requests` - HTTP library
- `python-dotenv` - Environment variable management
- `pandas` & `numpy` - Data processing

### Azure SDK
- `azure-ai-formrecognizer` - Azure Form Recognizer/Document Intelligence
- `azure-storage-blob` - Azure Blob Storage
- `azure-identity` - Azure authentication

### Development Tools
- `pytest` - Testing framework
- `black` - Code formatter
- `flake8` - Linting
- `pylint` - Static analysis
- `jupyter` - Notebook support

### Web Development (Optional)
- `flask` - Lightweight web framework
- `fastapi` - Modern API framework
- `uvicorn` - ASGI server

## 🚀 Development Workflow

1. **Code Formatting**: Code is automatically formatted with Black
2. **Linting**: Flake8 and Pylint provide code quality checks
3. **Testing**: Use pytest for unit tests
4. **Notebooks**: Jupyter notebooks are supported for data exploration

## 🔧 Customization

To add more packages:
1. Update `requirements.txt`
2. Rebuild the container: Command Palette → "Dev Containers: Rebuild Container"

To add VS Code extensions:
1. Update the `extensions` array in `.devcontainer/devcontainer.json`
2. Rebuild the container

## 📝 Environment Variables

Copy `.env.example` to `.env` and configure:

- **Azure Service Principal**: `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`
- **Form Recognizer**: `AZURE_FORM_RECOGNIZER_ENDPOINT`, `AZURE_FORM_RECOGNIZER_KEY`
- **Storage Account**: `AZURE_STORAGE_ACCOUNT_NAME`, `AZURE_STORAGE_ACCOUNT_KEY`

## 🏗️ Project Structure

```
.
├── .devcontainer/
│   ├── devcontainer.json    # Dev container configuration
│   └── Dockerfile           # Custom container setup
├── .env.example             # Environment variables template
├── requirements.txt         # Python dependencies
├── main.py                  # Sample application entry point
└── README.md               # This file
```

## 🆘 Troubleshooting

**Container won't start?**
- Check Docker is running
- Try "Dev Containers: Rebuild Container"

**Import errors?**
- Ensure the container has finished building
- Check if packages are listed in `requirements.txt`

**Azure authentication issues?**
- Verify your `.env` file configuration
- Check Azure CLI login: `az login`
