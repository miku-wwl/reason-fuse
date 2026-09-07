# Hosted-agent deployment needs data-plane management rights in addition to Owner.
resource "azurerm_role_assignment" "operator_project_manager" {
  count                = var.principal_id == "" ? 0 : 1
  scope                = azapi_resource.project.id
  role_definition_name = "Foundry Project Manager"
  principal_id         = var.principal_id
  principal_type       = var.principal_type
}

resource "azurerm_role_assignment" "operator_model_user" {
  count                = var.principal_id == "" ? 0 : 1
  scope                = azapi_resource.foundry_account.id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = var.principal_id
  principal_type       = var.principal_type
}
