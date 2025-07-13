data "azurerm_resource_group" "ai" {
  name = var.resource_group_name
}

data "azurerm_subscription" "current" {}
