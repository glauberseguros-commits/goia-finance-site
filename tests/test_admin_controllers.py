from controllers.admin_controller import AdminController
from controllers.admin_auditoria_controller import AdminAuditoriaController

def test_admin_controllers():

    assert hasattr(AdminController, "metricas")
    assert hasattr(AdminController, "assinantes")
    assert hasattr(AdminController, "buscar")
    assert hasattr(AdminController, "alterar_status")
    assert hasattr(AdminController, "alterar_plano")
    assert hasattr(AdminController, "excluir")

    assert hasattr(AdminAuditoriaController, "listar")

    print("OK - Controllers administrativos válidos.")

if __name__ == "__main__":
    test_admin_controllers()
