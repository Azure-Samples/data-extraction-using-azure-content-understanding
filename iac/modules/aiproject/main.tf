resource "random_string" "project_name_suffix" {
  length  = 6
  special = false
  upper   = false
}

module "project" {
  source                  = "Azure/avm-res-machinelearningservices-workspace/azurerm"
  version                 = "0.7.0"
  kind                    = "Project"
  location                = var.location
  resource_group_name     = var.resource_group_name
  name                    = "${var.project_name}-${random_string.project_name_suffix.result}"
  workspace_description   = var.project_description
  workspace_friendly_name = var.project_friendly_name
  ai_studio_hub_id        = local.hub_resource_id
  workspace_managed_network = var.workspace_managed_network
}
