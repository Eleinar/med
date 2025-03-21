from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QDialog, QLineEdit, QLabel, QMessageBox, QComboBox
from sqlalchemy.orm import Session
from models import User, Role, UserRole

class EditUserDialog(QDialog):
    def __init__(self, session: Session, user: User, parent=None):
        super().__init__(parent)
        self.session = session
        self.user = user
        self.setWindowTitle("Редактирование пользователя")
        self.setGeometry(200, 200, 400, 200)

        # Основной layout
        layout = QVBoxLayout()

        # Форма для редактирования пользователя
        form_layout = QVBoxLayout()
        self.username_input = QLineEdit(self)
        self.username_input.setText(user.username)
        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Введите новый пароль (оставьте пустым, чтобы не менять)")
        self.password_input.setEchoMode(QLineEdit.Password)

        # Получаем текущую роль пользователя
        user_role = self.session.query(UserRole).filter_by(user_id=user.id).first()
        current_role = self.session.query(Role).filter_by(id=user_role.role_id).first() if user_role else None
        current_role_name = current_role.name if current_role else "Basic User"

        self.role_combo = QComboBox(self)
        self.role_combo.addItems(["Basic User", "Administrator", "Sales Manager", "Worker", "Accountant", "Director"])
        self.role_combo.setCurrentText(current_role_name)

        form_layout.addWidget(QLabel("Имя пользователя:"))
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(QLabel("Пароль:"))
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(QLabel("Роль:"))
        form_layout.addWidget(self.role_combo)
        layout.addLayout(form_layout)

        # Кнопка сохранения
        self.save_button = QPushButton("Сохранить", self)
        self.save_button.clicked.connect(self.save_user)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def save_user(self):
        """Сохраняет изменения в пользователе."""
        try:
            new_username = self.username_input.text().strip()
            new_password = self.password_input.text().strip()
            new_role_name = self.role_combo.currentText()

            if not new_username:
                QMessageBox.warning(self, "Ошибка", "Имя пользователя не может быть пустым")
                return

            # Проверка уникальности имени пользователя
            existing_user = self.session.query(User).filter_by(username=new_username).filter(User.id != self.user.id).first()
            if existing_user:
                QMessageBox.warning(self, "Ошибка", "Пользователь с таким именем уже существует")
                return

            # Проверка существования роли
            new_role = self.session.query(Role).filter_by(name=new_role_name).first()
            if not new_role:
                QMessageBox.warning(self, "Ошибка", f"Роль {new_role_name} не найдена в базе данных")
                return

            # Обновление имени пользователя
            self.user.username = new_username

            # Обновление пароля, если он указан
            if new_password:
                self.user.password_hash = User.hash_password(new_password)

            # Обновление роли
            user_role = self.session.query(UserRole).filter_by(user_id=self.user.id).first()
            if user_role:
                user_role.role_id = new_role.id
            else:
                # Если у пользователя нет роли, создаём новую связь
                new_user_role = UserRole(user_id=self.user.id, role_id=new_role.id)
                self.session.add(new_user_role)

            self.session.commit()
            QMessageBox.information(self, "Успех", "Пользователь успешно обновлён")
            self.accept()

        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении пользователя: {e}")