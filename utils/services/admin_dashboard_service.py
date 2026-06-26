import pandas as pd

from controllers.admin_dashboard_controller import AdminDashboardController


def obter_dashboard_admin():

    metricas = AdminDashboardController.metricas()

    assinantes = AdminDashboardController.assinantes()

    if isinstance(assinantes, pd.DataFrame):
        total = len(assinantes)
    else:
        total = 0

    return {
        "metricas": metricas,
        "assinantes": assinantes,
        "total_assinantes": total,
    }
