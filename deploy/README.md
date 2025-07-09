# Terraform Data Extraction Infrastructure

This directory contains Terraform configuration files to deploy the Azure infrastructure required for the data extraction project using Azure AI Foundry with Content Understanding.

## Resources Created

- **Resource Group**: Container for all resources
- **CosmosDB Account**: NoSQL database for storing extracted data and metadata
  - Database: `documents`
  - Containers: `extracted-data`, `document-metadata`
- **Azure AI Foundry Hub**: Central hub for AI services (uses System-Assigned managed identity)
- **Azure AI Foundry Project**: Project workspace for Content Understanding capabilities
- **Storage Account**: Blob storage for document processing
  - Containers: `input-documents`, `processed-documents`
- **Key Vault**: Secure storage for connection strings and IDs

## Important Notes

- **Regional Availability**: Content Understanding is only available in specific regions:
  - West US (`westus`)
  - Sweden Central (`swedencentral`) 
  - Australia East (`australiaeast`)
- **Service Type**: Uses Azure AI Foundry Hub and Project resources (requires Azure Provider v4.35+)

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
| `location` | Azure region (West US, Sweden Central, or Australia East) | "West US" | No |
| `tags` | Resource tags | See variables.tf | No |
| `cosmos_consistency_level` | CosmosDB consistency level | "Session" | No |
| `storage_account_tier` | Storage account tier | "Standard" | No |
| `storage_replication_type` | Storage replication type | "LRS" | No |

## Outputs

After successful deployment, Terraform will output:

- Resource names and endpoints
- Connection information for applications
- Key Vault URI for accessing secrets

## Security

- All sensitive values (connection strings, API keys) are stored in Azure Key Vault
- Storage containers have private access by default
- CosmosDB is configured with Session consistency for optimal performance

## Cost Optimization

- CosmosDB is configured with serverless billing model
- Storage uses Standard tier with LRS replication
- AI Foundry Hub uses System-Assigned managed identity for secure access to storage and key vault

## Clean Up

To destroy the infrastructure:

```bash
terraform destroy
```

## Troubleshooting

1. **Authentication issues**: Ensure you're logged in with `az login`
2. **Permission errors**: Verify you have Contributor role on the subscription
3. **Resource name conflicts**: The configuration uses random suffixes to avoid conflicts
4. **Quota limits**: Check Azure quotas for Cognitive Services in your region

## Next Steps

After deployment, update your application configuration with the output values:

1. Get the outputs: `terraform output`
2. Configure your application with the connection strings from Key Vault
3. Update your code to use the created resource endpoints
