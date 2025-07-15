# https://azure.github.io/Azure-Verified-Modules/specs/terraform/#id-tffr2---category-outputs---additional-terraform-outputs
output "output" {
  description = "The azureopenai module"
  value       = module.azureopenai
}


output "private_endpoints" {
  description = "The azureopenai module"
  value       = module.azureopenai.private_endpoints
}
