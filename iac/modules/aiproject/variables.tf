variable "location" {
  description = "The location where the AI project will be deployed"
  type        = string
}

# This is required for most resource modules
variable "resource_group_name" {
  type        = string
  description = "The resource group where the resources will be deployed."
}

variable "hub_name" {
  type        = string
  description = "The name of the AI Foundry to deploy projects into."
}

variable "project_name" {
  description = "The name of the AI project"
  type        = string
}

variable "project_description" {
  description = "The description of the AI project"
  type        = string
}

variable "project_friendly_name" {
  description = "The friendly name of the AI project"
  type        = string
}

variable "workspace_managed_network" {
  type = object({
    isolation_mode = string
    spark_ready    = optional(bool, true)
  })
  default = {
    isolation_mode = "Disabled"
    spark_ready    = true
  }
  description = <<DESCRIPTION
Specifies properties of the workspace's managed virtual network.

Possible values for `isolation_mode` are:
- 'Disabled': Inbound and outbound traffic is unrestricted _or_ BYO VNet to protect resources.
- 'AllowInternetOutbound': Allow all internet outbound traffic.
- 'AllowOnlyApprovedOutbound': Outbound traffic is allowed by specifying service tags.
While is possible to update the workspace to enable network isolation ('AllowInternetOutbound' or 'AllowOnlyApprovedOutbound'), it is not possible to disable it on a workspace with it enabled.

`spark_ready` determines whether spark jobs will be run on the network. This value can be updated in the future.
DESCRIPTION
}