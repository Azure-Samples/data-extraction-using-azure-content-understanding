# Create a resource group
resource "azurerm_resource_group" "this" {
  location = var.resource_group_location
  name     = local.resource_group_name
}

# Create a random string for the resource name
resource "random_string" "name" {
  length  = 5
  numeric = false
  special = false
  upper   = false
}

module "naming" {
  source  = "Azure/naming/azurerm"
  version = "0.4.2"
  prefix  = ["${local.resource_prefix}"]
}

# Retrieve information about the current Azure client configuration
data "azurerm_client_config" "current" {}

# customer managed key encryption
resource "azurerm_user_assigned_identity" "cmk" {
  count               = var.use_customer_managed_key_encryption ? 1 : 0
  location            = azurerm_resource_group.this.location
  name                = module.naming.user_assigned_identity.name
  resource_group_name = azurerm_resource_group.this.name
}

module "cmk_key_vault" {
  source              = "Azure/avm-res-keyvault-vault/azurerm"
  version             = "0.10.0"
  location            = azurerm_resource_group.this.location
  name                = local.key_vault_name
  resource_group_name = azurerm_resource_group.this.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  network_acls = {
    default_action = "Allow"
  }
  public_network_access_enabled = true
  role_assignments = {
    deployment_user_secrets = {
      role_definition_id_or_name = "/providers/Microsoft.Authorization/roleDefinitions/14b46e9e-c2b7-41b4-b07b-48a6ebf60603" # Key Vault Crypto Officer
      principal_id               = data.azurerm_client_config.current.object_id
    }

    cosmos_db = {
      role_definition_id_or_name       = "/providers/Microsoft.Authorization/roleDefinitions/e147488a-f6f5-4113-8e2d-b22465e65bf6" # Key Vault Crypto Service Encryption User
      principal_id                     = "a232010e-820c-4083-83bb-3ace5fc29d0b"                                                    # CosmosDB
      skip_service_principal_aad_check = true                                                                                      # because it isn't a traditional SP
    }

    uai = {
      role_definition_id_or_name = "/providers/Microsoft.Authorization/roleDefinitions/14b46e9e-c2b7-41b4-b07b-48a6ebf60603" # Key Vault Crypto Officer
      principal_id               = azurerm_user_assigned_identity.cmk[0].principal_id
    }
  }
  tags = local.tags

  count = var.use_customer_managed_key_encryption ? 1 : 0
}

resource "azurerm_key_vault_key" "cmk" {
  count = var.use_customer_managed_key_encryption ? 1 : 0
  key_opts = [
    "decrypt",
    "encrypt",
    "sign",
    "unwrapKey",
    "verify",
    "wrapKey"
  ]
  key_type     = "RSA"
  key_vault_id = module.cmk_key_vault[0].resource_id
  name         = local.key_vault_name
  key_size     = 2048

  depends_on = [module.cmk_key_vault]
}


# Log Analytics Workspace
module "log_analytics_workspace" {
  source                                         = "./modules/loganalytics"
  name                                           = module.naming.log_analytics_workspace.name
  location                                       = azurerm_resource_group.this.location
  resource_group_name                            = azurerm_resource_group.this.name
  tags                                           = local.tags
  enable_telemetry                               = var.enable_telemetry
  log_analytics_workspace_cmk_for_query_forced   = var.use_customer_managed_key_encryption ? true : false
}

# Key Vault
module "key_vault" {
  source              = "./modules/keyvault"
  name                = local.key_vault_name
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  enable_telemetry    = var.enable_telemetry
  diagnostic_settings = local.diagnostic_settings
  public_network_access_enabled = true
  tags                = local.tags

  role_assignments = {
    current_user = {
      role_definition_id_or_name = "Key Vault Administrator"
      description                = "Full access to Key Vault for current user"
      principal_id               = data.azurerm_client_config.current.object_id
    }
  }

  depends_on = [module.log_analytics_workspace]
}

module "ai" {
  source                              = "./modules/ai"
  location                            = azurerm_resource_group.this.location
  name                                = lower(local.resource_prefix)
  kind                                = "Hub"
  resource_group_name                 = azurerm_resource_group.this.name
  container_registry_name             = null
  container_registry_resource_id      = null
  key_vault_name                      = module.key_vault.output.name
  key_vault_resource_id               = module.key_vault.output.resource_id
  tags                                = local.tags
  log_analytics_workspace_resource_id = module.log_analytics_workspace.output.resource_id
  diagnostic_settings                 = local.diagnostic_settings
  deploy_ai_search                    = false
  deploy_aoai                         = true
  deploy_ai_projects                  = true
  # if you set the deploy_ai_projects to true, you need to set the ai_projects variable
  ai_projects               = local.ai_projects
  deploy_ai_services        = var.deploy_ai_services
  create_compute_instance   = false
  workspace_managed_network = var.foundry_managed_network
  cognitive_deployments     = var.cognitive_deployments
  ds_access_roles           = local.ds_access_roles
  ds_group_members          = local.ds_group_members

  customer_managed_key = var.use_customer_managed_key_encryption ? {
    key_name               = azurerm_key_vault_key.cmk[0].name
    key_vault_resource_id  = module.cmk_key_vault.resource_id
    user_assigned_identity = { resource_id = azurerm_user_assigned_identity.cmk[0].id }
  } : null
  infrastructure_encryption_enabled = var.infrastructure_encryption_enabled

  # AML requires an instance of Application Insights, if set to false, an existing
  # instance resource needs to be passed in the variable application_insights_resource_id
  # in the core module
  deploy_app_insights_for_aml                   = var.deploy_app_insights_for_foundry
  ai_app_insights_local_authentication_disabled = var.ai_app_insights_local_authentication_disabled
  ai_app_insights_internet_ingestion_enabled    = var.ai_app_insights_internet_ingestion_enabled
  ai_app_insights_internet_query_enabled        = var.ai_app_insights_internet_query_enabled

  aml_storage_account_name        = lower(local.aml_storage_account_name)
  ai_app_insights_name            = lower(local.ai_app_insights_name)
  machine_learning_workspace_name = lower(local.machine_learning_workspace_name)
  aiservices_name                 = lower(local.aiservices_name)

  depends_on = [module.log_analytics_workspace]
}

module "cosmosdb" {
  source = "./modules/cosmos_db"

  resource_group_name                     = azurerm_resource_group.this.name
  location                                = azurerm_resource_group.this.location
  name                                    = local.cosmosdb_name
  analytical_storage_enabled              = true
  public_network_access_enabled           = true
  private_endpoints_manage_dns_zone_group = false
  mongo_server_version                    = "4.2"

  geo_locations = [
    {
      location          = azurerm_resource_group.this.location
      failover_priority = 0
      zone_redundant    = false
    }
  ]

  managed_identities = {
    type = "SystemAssigned"
  }

  capabilities = [
    {
      name = "EnableMongo"
    },
    {
      name = "EnableMongoRoleBasedAccessControl"
    },
    {
      name = "EnableMongoRetryableWrites"
    }
  ]
  mongo_databases = var.cosmosdb_mongo_databases

  # Role assignments for CosmosDB access
  role_assignments = {
    current_user = {
      role_definition_id_or_name = "DocumentDB Account Contributor"
      description                = "Current user access to MongoDB CosmosDB"
      principal_id               = data.azurerm_client_config.current.object_id
    }
    function_app = {
      role_definition_id_or_name = "DocumentDB Account Contributor"
      description                = "Function App access to MongoDB CosmosDB"
      principal_id               = module.app_service.app_service_identity_principal_id
    }
  }

  enable_telemetry    = var.enable_telemetry
  diagnostic_settings = local.diagnostic_settings
  tags                = local.tags
}

# Knowledge Base CosmosDB (SQL API)
module "cosmosdb_knowledge_base" {
  source = "./modules/cosmos_db"

  resource_group_name                     = azurerm_resource_group.this.name
  location                                = azurerm_resource_group.this.location
  name                                    = local.cosmosdb_knowledge_base_name
  analytical_storage_enabled              = true
  public_network_access_enabled           = true
  private_endpoints_manage_dns_zone_group = false

  geo_locations = [
    {
      location          = azurerm_resource_group.this.location
      failover_priority = 0
      zone_redundant    = false
    }
  ]

  managed_identities = {
    type = "SystemAssigned"
  }

  # SQL API databases with containers
  sql_databases = {
    "knowledge-base-db" = {
      name = "knowledge-base-db"
      containers = {
        "chat-history" = {
          name                = "chat-history"
          partition_key_paths = ["/id"]
          throughput          = 400
        }
      }
    }
  }

  # Role assignments for CosmosDB access
  role_assignments = {
    current_user = {
      role_definition_id_or_name = "DocumentDB Account Contributor"
      description                = "Current user access to Knowledge Base CosmosDB"
      principal_id               = data.azurerm_client_config.current.object_id
    }
    function_app = {
      role_definition_id_or_name = "DocumentDB Account Contributor"
      description                = "Function App access to Knowledge Base CosmosDB"
      principal_id               = module.app_service.app_service_identity_principal_id
    }
  }

  enable_telemetry    = var.enable_telemetry
  diagnostic_settings = local.diagnostic_settings
  tags                = local.tags
}

module "app_service" {
  source              = "./modules/function_app"
  location            = azurerm_resource_group.this.location
  app_name            = local.function_app_name
  env                 = var.environment_name
  resource_group_name = azurerm_resource_group.this.name
  tags                = local.tags

  # App Service configuration
  kind                        = "functionapp" # Fixed format for function app kind
  os_type                     = "Linux"
  functions_extension_version = "~4"
  function_app_site_config = {
    always_on                 = true
    pre_warmed_instance_count = 1
    application_stack = {
      "python" = {
        python_version = "3.11"
      }
    }
  }

  app_plan_sku_name           = "P1v2"
  enable_application_insights = true
  instance_memory_in_mb       = 2048
  function_app_uses_fc1       = false

  auto_heal_setting = {
    setting_1 = {
      action = {
        action_type                    = "Recycle"
        minimum_process_execution_time = "00:01:00"
      }
      trigger = {
        requests = {
          request = {
            count    = 100
            interval = "00:00:30"
          }
        }
        status_code = {
          status_5000 = {
            count             = 5000
            interval          = "00:05:00"
            path              = "/HealthCheck"
            status_code_range = 500
            sub_status        = 0
          }
          status_6000 = {
            count             = 6000
            interval          = "00:05:00"
            path              = "/Get"
            status_code_range = 500
            sub_status        = 0
          }
        }
      }
    }
  }
  application_insights = {
    workspace_resource_id = module.log_analytics_workspace.output.resource_id
  }

  diagnostic_settings = local.diagnostic_settings

  # Fix storage account reference - use AI module's storage account
  storage_account_name = data.azurerm_storage_account.ai_storage.name
  depends_on           = [module.ai.output]
}

# Add this data source to get the storage account key
data "azurerm_storage_account" "ai_storage" {
  name                = module.ai.output.storage_account.name
  resource_group_name = azurerm_resource_group.this.name
  depends_on          = [module.ai.output]
}

# SQL Role assignments for Knowledge Base CosmosDB (SQL API) - Built-in Data Contributor

# Current user SQL Role assignment for Knowledge Base CosmosDB (SQL API)
resource "azurerm_cosmosdb_sql_role_assignment" "current_user_cosmosdb_sql" {
  resource_group_name = azurerm_resource_group.this.name
  account_name        = module.cosmosdb_knowledge_base.output.name
  role_definition_id  = "/subscriptions/${var.subscription_id}/resourceGroups/${azurerm_resource_group.this.name}/providers/Microsoft.DocumentDB/databaseAccounts/${module.cosmosdb_knowledge_base.output.name}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002" # Cosmos DB Built-in Data Contributor
  principal_id        = data.azurerm_client_config.current.object_id
  scope               = module.cosmosdb_knowledge_base.output.resource_id
}

# Function App SQL Role assignment for Knowledge Base CosmosDB (SQL API)
resource "azurerm_cosmosdb_sql_role_assignment" "function_app_cosmosdb_sql" {
  resource_group_name = azurerm_resource_group.this.name
  account_name        = module.cosmosdb_knowledge_base.output.name
  role_definition_id  = "/subscriptions/${var.subscription_id}/resourceGroups/${azurerm_resource_group.this.name}/providers/Microsoft.DocumentDB/databaseAccounts/${module.cosmosdb_knowledge_base.output.name}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002" # Cosmos DB Built-in Data Contributor
  principal_id        = module.app_service.app_service_identity_principal_id
  scope               = module.cosmosdb_knowledge_base.output.resource_id
}

# Role assignments for AI Services access
resource "azurerm_role_assignment" "function_app_ai_services" {
  count                = var.deploy_ai_services ? 1 : 0
  scope                = module.ai.ai_services_resource.resource_id
  role_definition_name = "Cognitive Services User"
  principal_id         = module.app_service.app_service_identity_principal_id
  description          = "Function App access to AI Services"
}

resource "azurerm_role_assignment" "current_user_ai_services" {
  count                = var.deploy_ai_services ? 1 : 0
  scope                = module.ai.ai_services_resource.resource_id
  role_definition_name = "Cognitive Services User"
  principal_id         = data.azurerm_client_config.current.object_id
  description          = "Current user access to AI Services"
}
