data "azurerm_machine_learning_workspace" "ai_hub" {
  name                = var.hub_name
  resource_group_name = var.resource_group_name
}
