# Define resource names

locals {
  machine_learning_workspace_name                                = length(var.machine_learning_workspace_name) > 0 ? var.machine_learning_workspace_name : replace("aml${var.name}", "/[^a-zA-Z0-9-]/", "")
  aml_storage_account_name                                       = length(var.aml_storage_account_name) > 0 ? var.aml_storage_account_name : replace("sa${var.name}", "/[^a-zA-Z0-9-]/", "")
  aiservices_name                                                = length(var.aiservices_name) > 0 ? var.aiservices_name : replace("ais${var.name}", "/[^a-z0-9-]/", "")
  azureopenai_name                                               = length(var.azureopenai_name) > 0 ? var.azureopenai_name : replace("aoai${var.name}", "/[^a-z0-9-]/", "")
  ai_app_insights_name                                           = length(var.ai_app_insights_name) > 0 ? var.ai_app_insights_name : replace("appins${var.name}", "/[^a-zA-Z0-9-]/", "")
  outbound_rules = merge(
    var.deploy_aoai ? {
      openaiAccount = {
        resource_id         = module.azure_openai[0].output.resource_id
        sub_resource_target = "account"
      }
    } : {}
  )
}
