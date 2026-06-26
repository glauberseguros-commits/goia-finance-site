from controllers.admin_controller import AdminController


class AdminDashboardController:

    @staticmethod
    def metricas():
        return AdminController.metricas()

    @staticmethod
    def assinantes():
        return AdminController.assinantes()
