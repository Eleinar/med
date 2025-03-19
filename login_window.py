from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from models import create_connection, User, Role, UserRole
from admin_window import AdminWindow
from user_window import UserWindow

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.session = create_connection()
        self.setWindowTitle("Авторизация")
        self.setGeometry(100, 100, 300, 200)

        # Центральный виджет и layout
        widget = QWidget()
        layout = QVBoxLayout()

        # Поля ввода
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
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Введите имя пользователя и пароль")
            return

        # Поиск пользователя
        user = self.session.query(User).filter_by(username=username).first()
        if user and user.check_password(password):
            # Проверка роли
            user_role = self.session.query(UserRole).filter_by(user_id=user.id).first()
            if user_role:
                role = self.session.query(Role).filter_by(id=user_role.role_id).first()
                if role:
                    if role.name == "admin":
                        # Открытие интерфейса администратора
                        self.admin_window = AdminWindow(self.session)
                        self.admin_window.show()
                        self.hide()
                    elif role.name == "user":
                        # Открытие интерфейса обычного пользователя
                        self.user_window = UserWindow(self.session)
                        self.user_window.show()
                        self.hide()
                    else:
                        QMessageBox.warning(self, "Ошибка", f"Роль '{role.name}' не поддерживается")
                else:
                    QMessageBox.warning(self, "Ошибка", "Роль пользователя не определена")
            else:
                QMessageBox.warning(self, "Ошибка", "Роль пользователя не определена")
        else:
            QMessageBox.warning(self, "Ошибка", "Неверное имя пользователя или пароль")