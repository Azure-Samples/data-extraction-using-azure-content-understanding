# Terraform Data Extraction Infrastructure

This directory contains Terraform configuration files to deploy the Azure infrastructure required for the data extraction project using Azure AI Foundry with Content Understanding, Azure OpenAI, and serverless document processing.

## Resources Created

- **Resource Group**: Container for all resources
- **CosmosDB Account**: MongoDB API database for storing extracted data and metadata
  - Database: `documents`
  - Collections: `Lease_Documents`, `Configurations`
- **Azure AI Foundry Hub**: Central hub for AI services (uses System-Assigned managed identity)
- **Azure AI Foundry Project**: Project workspace for Content Understanding capabilities
- **Azure AI Services**: Cognitive services for Content Understanding
- **Azure OpenAI Service**: OpenAI service with GPT-4o (2024-11-20) model deployment
  - **GPT-4o Model**: Deploys the latest GPT-4o model (2024-11-20) for AI processing
- **Storage Accounts**: Multiple storage accounts for different purposes
  - **AI Foundry Storage**: For AI Foundry workspace
  - **Lease Documents Storage**: For Function App triggers and lease management
    - Container: `lease-documents`
  - **Function App Storage**: Dedicated storage for Azure Function runtime
- **Function App**: Azure Function with Python 3.11 runtime for document processing
- **Application Insights**: Monitoring and telemetry for the Function App
- **Key Vault**: Secure storage for connection strings, API keys, and configuration

## Prerequisites

1. **Azure CLI**: Install and login to Azure
   ```bash
   az login
   ```

2. **Terraform**: Install Terraform (version >= 1.0)

3. **Azure Subscription**: Ensure you have appropriate permissions to create resources

## Deployment Instructions

1. **Initialize Terraform**:
   ```bash
   cd deploy
   terraform init
   ```

2. **Create terraform.tfvars file**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```
   Edit `terraform.tfvars` with your desired configuration.

3. **Plan the deployment**:
   ```bash
   terraform plan
   ```

4. **Apply the configuration**:
   ```bash
   terraform apply
   ```

5. **Confirm the deployment** by typing `yes` when prompted.

## Configuration Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `subscription_id` | Azure subscription ID | - | Yes |
| `location` | Azure region (West US, Sweden Central, or Australia East) | "westus" | No |
| `tags` | Resource tags | See variables.tf | No |

**Note**: The `subscription_id` variable is marked as sensitive and must be provided in your `terraform.tfvars` file.

## Outputs

After successful deployment, Terraform will output:

- **Resource Information**: Names, endpoints, and IDs for all created resources
- **AI Services**: Azure AI Foundry Hub, Project, and OpenAI service details
- **Storage**: Connection strings and endpoints for all storage accounts
- **Database**: CosmosDB connection details and collection names
- **Function App**: Function App URL and configuration
- **Application Insights**: Monitoring configuration and connection strings
- **Key Vault**: URI and access information
- **App Configuration**: Consolidated configuration object with all application settings

All sensitive outputs are marked as sensitive and stored securely in Azure Key Vault.

## Security

- **Key Vault Integration**: All sensitive values (connection strings, API keys, database credentials) are stored in Azure Key Vault
- **Managed Identity**: Function App uses System-Assigned managed identity for secure access to Key Vault
- **Private Containers**: Storage containers have private access by default
- **Access Policies**: Key Vault configured with proper access policies for Terraform and Function App
- **Network Security**: Public network access enabled for management while maintaining security through access policies
- **Secret Management**: Automatic rotation and secure storage of all sensitive configuration

## Key Vault Secrets

The following secrets are automatically stored in Key Vault:

- `cosmosdb-connection-string`: CosmosDB connection string
- `cosmosdb-database-name`: Database name
- `lease-documents-collection-name`: Lease documents collection name
- `configurations-collection-name`: Configurations collection name
- `ai-foundry-endpoint`: AI Foundry service endpoint
- `ai-foundry-key`: AI Foundry access key
- `open-ai-endpoint`: Azure OpenAI service endpoint
- `open-ai-key`: Azure OpenAI access key
- `application-insights-connection-string`: Application Insights connection string
- `application-insights-key`: Application Insights instrumentation key
- `ai-foundry-storage-connection-string`: AI Foundry storage connection string
- `lease-storage-connection-string`: Lease documents storage connection string
- `function-app-storage-connection-string`: Function App storage connection string
- `function-app-url`: Function App URL

## Cost Optimization

- **CosmosDB**: Configured with serverless billing model and MongoDB API
- **Storage**: Uses Standard tier with LRS replication across multiple accounts
- **Function App**: Consumption (Y1) plan for automatic scaling and pay-per-execution
- **AI Services**: S0 tier for predictable costs
- **Managed Identity**: No additional costs for authentication and authorization
- **Application Insights**: Standard pricing with configurable data retention

## Clean Up

To destroy the infrastructure:

```bash
terraform destroy
```
