output "app_service_identity_client_id" {
  description = "The client ID of the user-assigned identity."
  value       = module.app_service_identity.client_id
}

output "app_service_identity_tenant_id" {
  description = "The tenant ID of the user-assigned identity."
  value       = module.app_service_identity.tenant_id
}

output "app_service_resource_id" {
  description = "The resource ID of the App Service."
  value       = module.app_service.resource_id
}

output "app_service_default_hostname" {
  description = "The default hostname of the App Service."
  value       = module.app_service.resource_uri
}

output "app_service_plan_id" {
  description = "The resource ID of the App Service Plan."
  value       = module.app_service_plan.resource_id
}

output "app_service_identity_resource_id" {
  description = "The resource ID of the user-assigned identity for the App Service."
  value       = module.app_service_identity.resource_id
}

output "service_plan_name" {
  description = "Full output of service plan created"
  value       = module.app_service_plan.name
}

output "service_hostname" {
  description = "The hostname of the App Service."
  value       = module.app_service.name
}

output "app_service_identity_principal_id" {
  description = "The principal ID of the user-assigned identity for the App Service."
  value       = module.app_service_identity.principal_id
}
