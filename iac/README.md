# Azure Data Extraction Infrastructure with Terraform

This directory contains Terraform configuration files to deploy a comprehensive Azure infrastructure for data extraction and AI-powered document processing using Azure AI Foundry, Azure OpenAI, CosmosDB, and serverless computing.

## Architecture Overview

The infrastructure deploys a modern, scalable solution for document processing and data extraction using:

- **Azure AI Foundry Hub & Projects**: Centralized AI service management
- **Azure OpenAI Service**: GPT-4o model for intelligent document processing
- **CosmosDB**: Dual database setup (MongoDB API + SQL API) for different data patterns
- **Azure Functions**: Serverless document processing pipeline
- **Key Vault**: Centralized secret management
- **Application Insights**: Comprehensive monitoring and telemetry

## Resources Created

### Core Infrastructure

| Resource Type | Example Name | Purpose |
|---------------|--------------|---------|
| **Resource Group** | `devdatextWuRg0` | Container for all resources |
| **Key Vault** | `devdatextWuKv0` | Secure storage for secrets and keys |
| **Log Analytics Workspace** | `devdatextWu-log` | Centralized logging and monitoring |

### AI & Machine Learning

| Resource Type | Example Name | Purpose |
|---------------|--------------|---------|
| **AI Foundry Hub** | `devdatextwu` | Central hub for AI services |
| **AI Foundry Project** | `devdatextWu-rag-project` | Project workspace for RAG capabilities |
| **Azure AI Services** | `devdatextWuais0` | Cognitive services for Content Understanding |
| **Azure OpenAI Service** | `devdatextWuaoai0` | OpenAI service with GPT-4o model |
| **Azure ML Workspace** | `devdatextWuaml0` | Machine learning workspace |

### Data Storage

| Resource Type | Example Name | Purpose |
|---------------|--------------|---------|
| **CosmosDB (MongoDB API)** | `devdatextwucosmos0` | Document storage with MongoDB API |
| **CosmosDB (SQL API)** | `devdatextwucosmoskb0` | Knowledge base with SQL API |
| **AI Storage Account** | `devdatextWusa0` | AI Foundry workspace storage |
| **Function Storage** | Auto-generated | Function App runtime storage |

### Compute & Processing

| Resource Type | Example Name | Purpose |
|---------------|--------------|---------|
| **Function App** | `devdatextwufunc0` | Serverless document processing |
| **App Service Plan** | Auto-generated | Function App hosting plan |
| **Application Insights** | `devdatextWuappins0` | Function monitoring and telemetry |

## Prerequisites

1. **Azure CLI**: Install and authenticate
   ```bash
   az login
   az account set --subscription "your-subscription-id"
   ```

2. **Terraform**: Install Terraform >= 1.0
   ```bash
   # On macOS with Homebrew
   brew install terraform
   
   # Verify installation
   terraform version
   ```

3. **Permissions**: Ensure you have Contributor access to the Azure subscription

## Quick Start

### 1. Initialize Terraform
```bash
cd /workspaces/data-extraction-using-azure-content-understanding/iac
terraform init
```

### 2. Configure Variables
Create your `terraform.tfvars` file:
```hcl
# Required variables
resource_group_location      = "eastus"
resource_group_location_abbr = "Wu"  # West US abbreviation
environment_name            = "dev"
usecase_name               = "datext"
subscription_id            = "your-subscription-id-here"
```

### 3. Plan and Deploy
```bash
# Review the deployment plan
terraform plan

# Deploy the infrastructure
terraform apply
```

### 4. Confirm Deployment
Type `yes` when prompted to confirm the deployment.

## Configuration Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `resource_group_location` | Azure region for deployment | `"eastus"` |
| `resource_group_location_abbr` | Region abbreviation for naming | `"Wu"` |
| `environment_name` | Environment name | `"dev"` |
| `usecase_name` | Use case identifier | `"datext"` |
| `subscription_id` | Azure subscription ID | `"12345678-1234-..."` |

## Key Vault Secrets

The following secrets should be manually stored in Key Vault (`devdatextWuKv0`):

### Database Connections
- `cosmosdb-connection-string`: MongoDB connection string for document storage

### AI Service Keys
- `azure-ai-services-api-key`: AI Services access key for Content Understanding
- `azure-openai-api-key`: OpenAI service access key for GPT-4o model

## Cleanup

To destroy all resources:

```bash
# Destroy infrastructure
terraform destroy

# Confirm destruction
# Type 'yes' when prompted
```

**Warning**: This will permanently delete all resources and data. Ensure you have backups if needed.