resource "azurerm_log_analytics_workspace" "validation" {
  name                = "log-rf-${local.resource_token}"
  location            = var.location
  resource_group_name = azurerm_resource_group.this.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_application_insights" "validation" {
  name                = "appi-rf-${local.resource_token}"
  location            = var.location
  resource_group_name = azurerm_resource_group.this.name
  application_type    = "web"
  workspace_id        = azurerm_log_analytics_workspace.validation.id
}

output "APPLICATIONINSIGHTS_CONNECTION_STRING" {
  value     = azurerm_application_insights.validation.connection_string
  sensitive = true
}
