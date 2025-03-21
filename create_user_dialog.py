from PySide6.QtWidgets import  QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox, QDialog
from models import User, Role, UserRole
from sqlalchemy.exc import SQLAlchemyError


class CreateUserDialog(QDialog):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.setWindowTitle("Создание нового пользователя")
        self.setGeometry(200, 200, 400, 200)

        # Основной layout
        layout = QVBoxLayout()

        # Форма для создания пользователя
        form_layout = QVBoxLayout()
        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("Имя пользователя")
        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.role_combo = QComboBox(self)
        self.role_combo.addItems(["Administrator", "Sales Manager", "Worker", "Accountant", "Director"])
        form_layout.addWidget(QLabel("Имя пользователя:"))
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(QLabel("Пароль:"))
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(QLabel("Роль:"))
        form_layout.addWidget(self.role_combo)
        layout.addLayout(form_layout)

        # Кнопка создания
        self.create_button = QPushButton("Создать", self)
        self.create_button.clicked.connect(self.create_user)
        layout.addWidget(self.create_button)

        self.setLayout(layout)

    def create_user(self):
        """Создаёт нового пользователя."""
        try:
            username = self.username_input.text().strip()
            password = self.password_input.text().strip()
            role_name = self.role_combo.currentText()

            if not username or not password:
                QMessageBox.warning(self, "Ошибка", "Заполните все поля")
                return

            # Проверка уникальности имени пользователя
            if self.session.query(User).filter_by(username=username).first():
                QMessageBox.warning(self, "Ошибка", "Пользователь с таким именем уже существует")
                return

            # Проверка существования роли
            role = self.session.query(Role).filter_by(name=role_name).first()
            if not role:
                QMessageBox.warning(self, "Ошибка", f"Роль {role_name} не найдена в базе данных")
                return

            # Создание пользователя
            new_user = User(
                username=username,
                password_hash=User.hash_password(password)
            )
            self.session.add(new_user)
            self.session.flush()

            # Связываем пользователя с ролью
            user_role = UserRole(user_id=new_user.id, role_id=role.id)
            self.session.add(user_role)

            self.session.commit()
            QMessageBox.information(self, "Успех", "Пользователь успешно создан")
            self.accept()

        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании пользователя: {e}")