variable "location" {
  type        = string
  description = "The location/region where the resources will be deployed."
  nullable    = false
}

variable "name" {
  type        = string
  description = "The name of the this resource."
}

# This is required for most resource modules
variable "resource_group_name" {
  type        = string
  description = "The resource group where the resources will be deployed."
}

variable "customer_managed_key" {
  type = object({
    key_vault_resource_id = string
    key_name              = string
    key_version           = optional(string, null)
    user_assigned_identity = optional(object({
      resource_id = string
    }), null)
  })
  default     = null
  description = "Specifies whether to use a customer-managed key for the ACR."
}

variable "user_assigned_identity_id" {
  type        = list(string)
  default     = null
  description = "The ID of the user assigned identity."
}

variable "key_vault_resource_id" {
  type        = string
  description = "The resource_id of the Azure Key Vault."
}

variable "enable_telemetry" {
  type        = bool
  default     = true
  description = <<DESCRIPTION
This variable controls whether or not telemetry is enabled for the module.
For more information see <https://aka.ms/avm/telemetryinfo>.
If it is set to false, then no telemetry will be collected.
As explained in the [AVM documentation](https://azure.github.io/Azure-Verified-Modules/help-support/telemetry/),
Microsoft relies on telemetry to identify the deployments of the AVM Modules.
Deployments are identified through a specific GUID (Globally Unique ID), indicating that the code originated from AVM.
The data is collected and governed by Microsoft’s privacy policies, found in the [Trust Center](https://www.microsoft.com/trust-center).
Telemetry collected does not provide Microsoft with insights into the resources deployed,
their configuration or any customer data stored in or processed by Azure resources deployed by using code from AVM.
Microsoft does not track the usage/consumption of individual resources using telemetry.
Telemetry collection is strictly optional, and it can easily be opted out of by following
[these procedures](https://azure.github.io/Azure-Verified-Modules/help-support/telemetry/#opting-out).
DESCRIPTION
}

variable "kind" {
  type        = string
  default     = "Default"
  description = <<DESCRIPTION
The kind of the resource. This is used to determine the type of the resource. If not specified, the resource will be created as a Default resource which is AML.
Possible values are:
- `Default` - The resource will be created as a standard Azure Machine Learning resource.
- `hub` - The resource will be created as an Azure AI Hub resource.
- `Project` - The resource will be created as an Azure AI project.
DESCRIPTION
}

variable "create_compute_instance" {
  type        = bool
  default     = false
  description = "Specifies whether a compute instance should be created for the workspace to provision the managed vnet."
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

variable "tags" {
  type        = map(string)
  default     = null
  description = "A map of tags to add to all resources"
}

variable "storage_account_resource_id" {
  type        = string
  description = "The resource_id of the storage account."
}

variable "container_registry_resource_id" {
  type        = string
  default     = ""
  description = "The resource_id of the Azure Container Registry."
}

variable "application_insights_resource_id" {
  type        = string
  default     = ""
  description = "The resource_id of the Application Insights instance."
}

variable "log_analytics_workspace_resource_id" {
  type        = string
  default     = ""
  description = "The resource_id of the Log Analytics Workspace."
}

# variable "diagnostic_settings" {
#   type = map(object({
#     name                  = optional(string, null)
#     workspace_resource_id = optional(string, null)
#   }))
# }

variable "outbound_rules" {
  type = map(object({
    resource_id         = string
    sub_resource_target = string
  }))
  default     = {}
  description = <<DESCRIPTION
  A map of private endpoints toutbound rules for the managed network.

  - `resource_id` - The resource id for the corresponding private endpoint.
  - `sub_resource_target` - The sub_resource_target is target for the private endpoint. e.g. account for Openai, searchService for Azure Ai Search

  DESCRIPTION
}

variable "aml_workspace_ds_adgroup_id" {
  type        = string
  default     = null
  description = "The object id of the data scientist group."
}

variable "aml_workspace_ml_operator_adgroup_id" {
  type        = string
  default     = null
  description = "The object id of the ML operator AD group."
}

variable "deploy_ai_services" {
  type        = bool
  default     = false
  description = "Specifies whether to deploy the AI services."
}

variable "ai_service_name" {
  type        = string
  default     = null
  description = "The name of the AI service."
}
