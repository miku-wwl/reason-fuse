variable "operations_admin_key" {
  type      = string
  sensitive = true
}

resource "azurerm_service_plan" "operations" {
  name                = "plan-rf-operations-${local.resource_token}"
  location            = var.location
  resource_group_name = azurerm_resource_group.this.name
  os_type             = "Linux"
  sku_name            = "F1"
}

resource "azurerm_linux_web_app" "operations" {
  name                = "rf-operations-${local.resource_token}"
  location            = var.location
  resource_group_name = azurerm_resource_group.this.name
  service_plan_id     = azurerm_service_plan.operations.id
  https_only          = true
  site_config {
    always_on        = false
    app_command_line = "python /home/site/wwwroot/server.py"
    application_stack {
      python_version = "3.13"
    }
  }
  app_settings = {
    OPERATIONS_ADMIN_KEY           = var.operations_admin_key
    SCM_DO_BUILD_DURING_DEPLOYMENT = "false"
  }
}

output "OPERATIONS_ENDPOINT" {
  value = "https://${azurerm_linux_web_app.operations.default_hostname}"
}

output "OPERATIONS_APP_NAME" {
  value = azurerm_linux_web_app.operations.name
}
