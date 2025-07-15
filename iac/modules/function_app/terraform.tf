terraform {
  required_version = ">= 1.9"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 4.0.0, < 5.0.0"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 3.3"
    }
    azapi = {
      source  = "Azure/azapi"
      version = ">= 1.14.0, < 3.0.0"
    }
  }
}
