def restart_service(service_name: str) -> dict:
    """R2 test action. Records a simulated restart; never touches a real service."""
    return {"service_name": service_name, "status": "SIMULATED_RESTART"}
