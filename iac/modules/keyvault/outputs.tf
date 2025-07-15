# https://azure.github.io/Azure-Verified-Modules/specs/terraform/#id-tffr2---category-outputs---additional-terraform-outputs
output "output" {
  description = "The Azure Key Vault module output."
  value       = module.key_vault
}
