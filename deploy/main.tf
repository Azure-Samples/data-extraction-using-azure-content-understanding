terraform {
  required_version = ">= 1.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.35"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

# Generate random suffix for unique resource names
resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "rg-data-extraction-${random_string.suffix.result}"
  location = var.location

  tags = var.tags
}

# CosmosDB Account with MongoDB API
resource "azurerm_cosmosdb_account" "main" {
  name                = "cosmos-data-extraction-${random_string.suffix.result}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  offer_type          = "Standard"
  kind                = "MongoDB"

  consistency_policy {
    consistency_level = "Session"
  }

  geo_location {
    location          = azurerm_resource_group.main.location
    failover_priority = 0
  }

  capabilities {
    name = "EnableServerless"
  }

  capabilities {
    name = "EnableMongo"
  }

  tags = var.tags
}

# CosmosDB MongoDB Database
resource "azurerm_cosmosdb_mongo_database" "main" {
  name                = "documents"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
}

# CosmosDB MongoDB Collection for Lease Documents
resource "azurerm_cosmosdb_mongo_collection" "lease_documents" {
  name                = "Lease_Documents"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_mongo_database.main.name

  default_ttl_seconds = -1
  shard_key           = "_id"

  index {
    keys   = ["_id"]
    unique = true
  }

  index {
    keys = ["document_id"]
  }

  index {
    keys = ["created_date"]
  }
}

# CosmosDB MongoDB Collection for Configurations
resource "azurerm_cosmosdb_mongo_collection" "configurations" {
  name                = "Configurations"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_mongo_database.main.name

  default_ttl_seconds = -1
  shard_key           = "_id"

  index {
    keys   = ["_id"]
    unique = true
  }

  index {
    keys = ["config_type"]
  }
}

# Storage Account for general document processing and AI Foundry
resource "azurerm_storage_account" "ai_foundry" {
  name                     = "staifoundry${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  
  blob_properties {
    cors_rule {
      allowed_headers    = ["*"]
      allowed_methods    = ["DELETE", "GET", "HEAD", "MERGE", "POST", "OPTIONS", "PUT", "PATCH"]
      allowed_origins    = ["*"]
      exposed_headers    = ["*"]
      max_age_in_seconds = 3600
    }
  }

  tags = var.tags
}

# Storage Account for lease documents (Function App triggers)
resource "azurerm_storage_account" "lease_documents" {
  name                     = "stlease${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  
  blob_properties {
    cors_rule {
      allowed_headers    = ["*"]
      allowed_methods    = ["DELETE", "GET", "HEAD", "MERGE", "POST", "OPTIONS", "PUT", "PATCH"]
      allowed_origins    = ["*"]
      exposed_headers    = ["*"]
      max_age_in_seconds = 3600
    }
  }

  tags = var.tags
}

# Storage Account for Function App
resource "azurerm_storage_account" "function_app" {
  name                     = "stfunc${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = var.tags
}

# App Service Plan for Function App
resource "azurerm_service_plan" "function_app" {
  name                = "asp-data-extraction-${random_string.suffix.result}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  sku_name            = "Y1"

  tags = var.tags
}

# Function App for document processing
resource "azurerm_linux_function_app" "main" {
  name                = "func-data-extract-${random_string.suffix.result}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  service_plan_id     = azurerm_service_plan.function_app.id

  storage_account_name       = azurerm_storage_account.function_app.name
  storage_account_access_key = azurerm_storage_account.function_app.primary_access_key

  site_config {
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME"       = "python"
    "AzureWebJobsFeatureFlags"       = "EnableWorkerIndexing"
  }

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

# Key Vault for storing secrets
resource "azurerm_key_vault" "main" {
  name                = "kv-data-extract-${random_string.suffix.result}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    key_permissions = [
      "Get", "List", "Create", "Delete", "Update", "Import", "Backup", "Restore"
    ]

    secret_permissions = [
      "Get", "List", "Set", "Delete", "Backup", "Restore", "Purge"
    ]

    certificate_permissions = [
      "Get", "List", "Create", "Delete", "Update", "Import", "Backup", "Restore"
    ]
  }

  # Access policy for Function App to read secrets
  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = azurerm_linux_function_app.main.identity[0].principal_id

    secret_permissions = [
      "Get"
    ]
  }

  tags = var.tags
}

# Azure AI Services for Content Understanding
resource "azurerm_ai_services" "main" {
  name                = "ai-services-${random_string.suffix.result}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku_name            = "S0"

  tags = var.tags
}

# Azure AI Foundry Hub
resource "azurerm_ai_foundry" "main" {
  name                = "aihub-${random_string.suffix.result}"
  location            = azurerm_ai_services.main.location
  resource_group_name = azurerm_resource_group.main.name
  storage_account_id  = azurerm_storage_account.ai_foundry.id
  key_vault_id        = azurerm_key_vault.main.id

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

# Azure AI Foundry Project for Content Understanding
resource "azurerm_ai_foundry_project" "main" {
  name               = "aiproject-${random_string.suffix.result}"
  location           = azurerm_ai_foundry.main.location
  ai_services_hub_id = azurerm_ai_foundry.main.id

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

# Storage Container for input documents
resource "azurerm_storage_container" "input_documents" {
  name                  = "input-documents"
  storage_account_name  = azurerm_storage_account.ai_foundry.name
  container_access_type = "private"
}

# Storage Container for processed documents
resource "azurerm_storage_container" "processed_documents" {
  name                  = "processed-documents"
  storage_account_name  = azurerm_storage_account.ai_foundry.name
  container_access_type = "private"
}

# Storage Container for lease documents (Function App triggers)
resource "azurerm_storage_container" "lease_documents" {
  name                  = "lease-documents"
  storage_account_name  = azurerm_storage_account.lease_documents.name
  container_access_type = "private"
}

# Store CosmosDB connection string in Key Vault
resource "azurerm_key_vault_secret" "cosmosdb_connection_string" {
  name         = "cosmosdb-connection-string"
  value        = "AccountEndpoint=${azurerm_cosmosdb_account.main.endpoint};AccountKey=${azurerm_cosmosdb_account.main.primary_key};"
  key_vault_id = azurerm_key_vault.main.id
}

# Store AI Services primary access key in Key Vault
resource "azurerm_key_vault_secret" "ai_services_key" {
  name         = "ai-foundry-key"
  value        = azurerm_ai_services.main.primary_access_key
  key_vault_id = azurerm_key_vault.main.id
}

# Store AI Foundry endpoint in Key Vault
resource "azurerm_key_vault_secret" "ai_foundry_endpoint" {
  name         = "ai-foundry-endpoint"
  value        = "https://${azurerm_ai_services.main.name}.services.ai.azure.com/"
  key_vault_id = azurerm_key_vault.main.id
}

# Store AI Foundry Storage Account connection string in Key Vault
resource "azurerm_key_vault_secret" "ai_foundry_storage_connection_string" {
  name         = "ai-foundry-storage-connection-string"
  value        = azurerm_storage_account.ai_foundry.primary_connection_string
  key_vault_id = azurerm_key_vault.main.id
}

# Store Lease Documents Storage Account connection string in Key Vault
resource "azurerm_key_vault_secret" "lease_storage_connection_string" {
  name         = "lease-storage-connection-string"
  value        = azurerm_storage_account.lease_documents.primary_connection_string
  key_vault_id = azurerm_key_vault.main.id
}

# Store Function App Storage Account connection string in Key Vault
resource "azurerm_key_vault_secret" "function_app_storage_connection_string" {
  name         = "function-app-storage-connection-string"
  value        = azurerm_storage_account.function_app.primary_connection_string
  key_vault_id = azurerm_key_vault.main.id
}

# Store Function App URL in Key Vault
resource "azurerm_key_vault_secret" "function_app_url" {
  name         = "function-app-url"
  value        = "https://${azurerm_linux_function_app.main.name}.azurewebsites.net"
  key_vault_id = azurerm_key_vault.main.id
}

# Store CosmosDB MongoDB database name in Key Vault
resource "azurerm_key_vault_secret" "cosmosdb_database_name" {
  name         = "cosmosdb-database-name"
  value        = azurerm_cosmosdb_mongo_database.main.name
  key_vault_id = azurerm_key_vault.main.id
}

# Store Lease Documents collection name in Key Vault
resource "azurerm_key_vault_secret" "lease_documents_collection_name" {
  name         = "lease-documents-collection-name"
  value        = azurerm_cosmosdb_mongo_collection.lease_documents.name
  key_vault_id = azurerm_key_vault.main.id
}

# Store Configurations collection name in Key Vault
resource "azurerm_key_vault_secret" "configurations_collection_name" {
  name         = "configurations-collection-name"
  value        = azurerm_cosmosdb_mongo_collection.configurations.name
  key_vault_id = azurerm_key_vault.main.id
}

# Data source for current Azure client configuration
data "azurerm_client_config" "current" {}
