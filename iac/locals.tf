locals {
  tags = {
    environment = var.environment_name
    usecase     = var.usecase_name
    cicd        = "terraform"
  }

  resource_prefix = "${var.environment_name}${var.usecase_name}${var.resource_group_location_abbr}"

  core_name = "${local.resource_prefix}core0"

  # The name of the resource group
  resource_group_name = "${local.resource_prefix}Rg0"

  # The name of the application insights
  application_insights_name = "${local.resource_prefix}Appi"

  # The name of the key vault
  key_vault_name = "${local.resource_prefix}Kv0"

  # The name of the storage account
  storage_account_name = "${local.resource_prefix}Sa0"

  # Log Analytics Name
  log_analytics_workspace_name = "${local.resource_prefix}Log0"

  # CosmosDB names
  cosmosdb_name                = lower("${local.resource_prefix}cosmos0")
  cosmosdb_knowledge_base_name = lower("${local.resource_prefix}cosmoskb0")

  # Function App name
  function_app_name = lower("${local.resource_prefix}func0")

  # AI module variables
  machine_learning_workspace_name = "${local.resource_prefix}aml0"
  aml_storage_account_name        = "${local.resource_prefix}sa0"
  azureopenai_name                = "${local.resource_prefix}aoai0"
  ai_app_insights_name            = "${local.resource_prefix}appins0"
  aiservices_name                 = "${local.resource_prefix}ais0"

  ai_projects = {
    rag_project = {
      name          = "${local.resource_prefix}-rag-project"
      description   = "AI Foundry RAG Project for ${local.resource_prefix} use case"
      friendly_name = "AI Foundry RAG Project"
    }
  }

  # Azure ML Data Scientist : Can perform all actions within an Azure Machine Learning workspace,
  #                           except for creating or deleting compute resources and modifying the workspace itself.
  # Azure ML Compute Contributor : Can access and perform CRUD operations on Machine Learning Services managed compute resources (including Notebook VMs).
  # Storage Blob Data Contributor : Can read and write to storage accounts
  # Search Index Data Contributor:  Load documents, run indexing jobs
  # Search Service Contributor : CRUD operations on Indexes
  # Cognitive Services OpenAI Contributor :Full access including the ability to fine-tune, deploy and generate text
  ds_access_roles = [
    "AzureML Data Scientist",
    "AzureML Compute Operator",
    "Storage Blob Data Contributor",
    "Storage File Data Privileged Contributor",
    "Search Index Data Contributor",
    "Search Service Contributor",
    "Cognitive Services OpenAI Contributor",
    "Cognitive Services OpenAI User",
    "Cognitive Services User"
  ]

  # Replace/Add the user object ids of the entra app or users to the group
  ds_group_members = [data.azurerm_client_config.current.object_id]
}

# Diagnostic settings
locals {
  diagnostic_settings = {
    defaultDiagnosticSettings = {
      name                  = "Send to Log Analytics (AllLogs, AllMetrics)"
      workspace_resource_id = module.log_analytics_workspace.output.resource_id
      logs = [
        {
          category = "AllLogs"
          enabled  = true
          retention_policy = {
            enabled = false
            days    = 0
          }
        },
        {
          category = "AllMetrics"
          enabled  = true
          retention_policy = {
            enabled = false
            days    = 0
          }
        }
      ]
    }
  }
}