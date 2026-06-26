from controllers.admin_controller import AdminController


def test_admin_controller_tem_metodos():
    assert hasattr(AdminController, "metricas")
    assert hasattr(AdminController, "assinantes")
    assert hasattr(AdminController, "buscar")
    assert hasattr(AdminController, "alterar_status")
    assert hasattr(AdminController, "alterar_plano")
    assert hasattr(AdminController, "excluir")
    assert hasattr(AdminController, "auditoria")
