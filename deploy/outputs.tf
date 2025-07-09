output "resource_group_name" {
  description = "The name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "cosmosdb_account_name" {
  description = "The name of the CosmosDB account"
  value       = azurerm_cosmosdb_account.main.name
}

output "cosmosdb_endpoint" {
  description = "The endpoint URL for the CosmosDB account"
  value       = azurerm_cosmosdb_account.main.endpoint
}

output "cosmosdb_database_name" {
  description = "The name of the CosmosDB MongoDB database"
  value       = azurerm_cosmosdb_mongo_database.main.name
}

output "cosmosdb_primary_key" {
  description = "The primary access key for CosmosDB"
  value       = azurerm_cosmosdb_account.main.primary_key
  sensitive   = true
}

output "lease_documents_collection_name" {
  description = "The name of the Lease Documents MongoDB collection"
  value       = azurerm_cosmosdb_mongo_collection.lease_documents.name
}

output "configurations_collection_name" {
  description = "The name of the Configurations MongoDB collection"
  value       = azurerm_cosmosdb_mongo_collection.configurations.name
}

output "ai_foundry_hub_name" {
  description = "The name of the AI Foundry Hub"
  value       = azurerm_ai_foundry.main.name
}

output "ai_foundry_hub_workspace_id" {
  description = "The workspace ID of the AI Foundry Hub"
  value       = azurerm_ai_foundry.main.workspace_id
}

output "ai_services_name" {
  description = "The name of the AI Services resource"
  value       = azurerm_ai_services.main.name
}

output "ai_services_endpoint" {
  description = "The endpoint URL for AI Services"
  value       = azurerm_ai_services.main.endpoint
}

output "ai_services_primary_access_key" {
  description = "The primary access key for AI Services"
  value       = azurerm_ai_services.main.primary_access_key
  sensitive   = true
}

output "ai_foundry_endpoint" {
  description = "The Azure AI Foundry endpoint for Content Understanding"
  value       = "https://${azurerm_ai_services.main.name}.services.ai.azure.com/"
}

output "ai_foundry_project_name" {
  description = "The name of the AI Foundry Project"
  value       = azurerm_ai_foundry_project.main.name
}

output "ai_foundry_project_id" {
  description = "The ID of the AI Foundry Project"
  value       = azurerm_ai_foundry_project.main.id
}

output "ai_foundry_storage_account_name" {
  description = "The name of the AI Foundry storage account"
  value       = azurerm_storage_account.ai_foundry.name
}

output "ai_foundry_storage_primary_connection_string" {
  description = "The primary connection string for the AI Foundry storage account"
  value       = azurerm_storage_account.ai_foundry.primary_connection_string
  sensitive   = true
}

output "ai_foundry_storage_primary_blob_endpoint" {
  description = "The primary blob endpoint for the AI Foundry storage account"
  value       = azurerm_storage_account.ai_foundry.primary_blob_endpoint
}

output "lease_storage_account_name" {
  description = "The name of the lease documents storage account"
  value       = azurerm_storage_account.lease_documents.name
}

output "lease_storage_primary_connection_string" {
  description = "The primary connection string for the lease documents storage account"
  value       = azurerm_storage_account.lease_documents.primary_connection_string
  sensitive   = true
}

output "lease_storage_primary_blob_endpoint" {
  description = "The primary blob endpoint for the lease documents storage account"
  value       = azurerm_storage_account.lease_documents.primary_blob_endpoint
}

output "lease_container_name" {
  description = "The name of the lease documents container"
  value       = azurerm_storage_container.lease_documents.name
}

output "key_vault_name" {
  description = "The name of the Key Vault"
  value       = azurerm_key_vault.main.name
}

output "key_vault_uri" {
  description = "The URI of the Key Vault"
  value       = azurerm_key_vault.main.vault_uri
}

output "function_app_name" {
  description = "The name of the Function App"
  value       = azurerm_linux_function_app.main.name
}

output "function_app_url" {
  description = "The URL of the Function App"
  value       = "https://${azurerm_linux_function_app.main.name}.azurewebsites.net"
}

output "function_app_storage_account_name" {
  description = "The name of the Function App storage account"
  value       = azurerm_storage_account.function_app.name
}

# Environment configuration for applications
output "app_config" {
  description = "Configuration values for applications"
  sensitive   = true
  value = {
    cosmosdb_endpoint                      = azurerm_cosmosdb_account.main.endpoint
    cosmosdb_database                      = azurerm_cosmosdb_mongo_database.main.name
    lease_documents_collection             = azurerm_cosmosdb_mongo_collection.lease_documents.name
    configurations_collection              = azurerm_cosmosdb_mongo_collection.configurations.name
    content_understanding_endpoint         = azurerm_ai_services.main.endpoint
    ai_foundry_hub_workspace_id            = azurerm_ai_foundry.main.workspace_id
    ai_foundry_project_id                  = azurerm_ai_foundry_project.main.id
    ai_foundry_storage_account_name        = azurerm_storage_account.ai_foundry.name
    ai_foundry_blob_endpoint               = azurerm_storage_account.ai_foundry.primary_blob_endpoint
    lease_storage_account_name             = azurerm_storage_account.lease_documents.name
    lease_blob_endpoint                    = azurerm_storage_account.lease_documents.primary_blob_endpoint
    lease_container                        = azurerm_storage_container.lease_documents.name
    key_vault_uri                          = azurerm_key_vault.main.vault_uri
    function_app_name                      = azurerm_linux_function_app.main.name
    function_app_url                       = "https://${azurerm_linux_function_app.main.name}.azurewebsites.net"
    openai_endpoint                        = azurerm_cognitive_account.openai.endpoint
    openai_deployment_name                 = azurerm_cognitive_deployment.gpt4o.name
    application_insights_key               = azurerm_application_insights.main.instrumentation_key
    application_insights_connection_string = azurerm_application_insights.main.connection_string
  }
}

# Azure OpenAI outputs
output "openai_endpoint" {
  description = "The endpoint for the Azure OpenAI service"
  value       = azurerm_cognitive_account.openai.endpoint
}

output "openai_key" {
  description = "The primary access key for the Azure OpenAI service"
  value       = azurerm_cognitive_account.openai.primary_access_key
  sensitive   = true
}

output "gpt4o_deployment_name" {
  description = "The name of the GPT-4o deployment"
  value       = azurerm_cognitive_deployment.gpt4o.name
}

# Application Insights outputs
output "application_insights_name" {
  description = "The name of the Application Insights instance"
  value       = azurerm_application_insights.main.name
}

output "application_insights_instrumentation_key" {
  description = "The instrumentation key for Application Insights"
  value       = azurerm_application_insights.main.instrumentation_key
  sensitive   = true
}

output "application_insights_connection_string" {
  description = "The connection string for Application Insights"
  value       = azurerm_application_insights.main.connection_string
  sensitive   = true
}

output "application_insights_app_id" {
  description = "The App ID for Application Insights"
  value       = azurerm_application_insights.main.app_id
}
