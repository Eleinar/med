from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from models import create_connection, User, Role, UserRole
from admin_window import AdminWindow
from user_window import UserWindow

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вход в систему")
        self.setGeometry(100, 100, 300, 200)

        # Центральный виджет и layout
        widget = QWidget()
        layout = QVBoxLayout()

        # Поля для ввода
        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("Имя пользователя")
        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.Password)

        # Кнопка входа
        self.login_button = QPushButton("Войти", self)
        self.login_button.clicked.connect(self.login)

        # Добавление элементов в layout
        layout.addWidget(QLabel("Вход в систему"))
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)

        widget.setLayout(layout)
        self.setCentralWidget(widget)



    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Введите имя пользователя и пароль")
            return

        # Проверка пользователя в базе
        session = create_connection()
        user = session.query(User).filter_by(username=username).first()

        if user and user.check_password(password):
            # Получаем роль пользователя
            user_role = session.query(UserRole).filter_by(user_id=user.id).first()
            role = session.query(Role).filter_by(id=user_role.role_id).first() if user_role else None
            role_name = role.name if role else "Basic User"

            # Приводим имя роли к значению, используемому в коде
            role_mapping = {
                "Basic User": "basic",
                "Administrator": "admin",
                "Sales Manager": "sales_manager",
                "Worker": "worker",
                "Accountant": "accountant",
                "Director": "director"
            }
            role_value = role_mapping.get(role_name, "basic")

            # В зависимости от роли открываем соответствующий интерфейс
            if role_value == "admin":
                self.admin_window = AdminWindow(session, user, role_value)
                self.admin_window.show()
            else:
                self.user_window = UserWindow(session, user, role_value)
                self.user_window.show()
            self.close()
        else:
            QMessageBox.critical(self, "Ошибка", "Неверное имя пользователя или пароль")
            session.close()