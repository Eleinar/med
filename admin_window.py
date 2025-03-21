from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QComboBox, QMessageBox
from models import User, Role, UserRole
from create_user_dialog import CreateUserDialog
from sqlalchemy.orm import Session
from edit_user_dialog import EditUserDialog

class AdminWindow(QMainWindow):
    def __init__(self, session: Session, user: User, role: str):
        super().__init__()
        self.session = session
        self.user = user
        self.role = role
        self.setWindowTitle("Интерфейс администратора - Управление пользователями")
        self.setGeometry(100, 100, 600, 400)

        # Центральный виджет и layout
        widget = QWidget()
        layout = QVBoxLayout()

        # Кнопки управления
        buttons_layout = QHBoxLayout()
        self.create_user_button = QPushButton("Создать пользователя")
        self.create_user_button.clicked.connect(self.open_create_user_dialog)
        self.edit_user_button = QPushButton("Редактировать пользователя")  # Новая кнопка
        self.edit_user_button.clicked.connect(self.open_edit_user_dialog)
        self.delete_user_button = QPushButton("Удалить пользователя")
        self.delete_user_button.clicked.connect(self.delete_user)
        buttons_layout.addWidget(self.create_user_button)
        buttons_layout.addWidget(self.edit_user_button)
        buttons_layout.addWidget(self.delete_user_button)
        layout.addLayout(buttons_layout)

        # Таблица пользователей
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(3)
        self.user_table.setHorizontalHeaderLabels(["ID", "Имя пользователя", "Роль"])
        layout.addWidget(self.user_table)

        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Загрузка пользователей
        self.load_users()

    def open_create_user_dialog(self):
        """Открывает диалоговое окно для создания пользователя."""
        dialog = CreateUserDialog(self.session, self)
        if dialog.exec():
            self.load_users()

    def open_edit_user_dialog(self):
        """Открывает диалоговое окно для редактирования пользователя."""
        selected_row = self.user_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя для редактирования")
            return

        user_id = int(self.user_table.item(selected_row, 0).text())
        user = self.session.query(User).filter_by(id=user_id).first()
        if not user:
            QMessageBox.warning(self, "Ошибка", "Пользователь не найден")
            return

        # Нельзя редактировать самого себя
        if user.id == self.user.id:
            QMessageBox.warning(self, "Ошибка", "Нельзя редактировать самого себя")
            return

        dialog = EditUserDialog(self.session, user, self)
        if dialog.exec():
            self.load_users()

    def delete_user(self):
        """Удаляет выбранного пользователя."""
        selected_row = self.user_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя для удаления")
            return

        user_id = int(self.user_table.item(selected_row, 0).text())
        user = self.session.query(User).filter_by(id=user_id).first()
        if not user:
            QMessageBox.warning(self, "Ошибка", "Пользователь не найден")
            return

        # Нельзя удалить самого себя
        if user.id == self.user.id:
            QMessageBox.warning(self, "Ошибка", "Нельзя удалить самого себя")
            return

        # Подтверждение удаления
        reply = QMessageBox.question(self, "Подтверждение", f"Вы уверены, что хотите удалить пользователя {user.username}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                # Удаляем связи с ролями
                self.session.query(UserRole).filter_by(user_id=user.id).delete()
                # Удаляем пользователя
                self.session.delete(user)
                self.session.commit()
                QMessageBox.information(self, "Успех", "Пользователь успешно удалён")
                self.load_users()
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении пользователя: {e}")

    def load_users(self):
        """Загружает список пользователей."""
        self.user_table.setRowCount(0)
        users = self.session.query(User).all()
        self.user_table.setRowCount(len(users))
        for row, user in enumerate(users):
            user_role = self.session.query(UserRole).filter_by(user_id=user.id).first()
            role = self.session.query(Role).filter_by(id=user_role.role_id).first() if user_role else None
            role_name = role.name if role else "Не указана"
            self.user_table.setItem(row, 0, QTableWidgetItem(str(user.id)))
            self.user_table.setItem(row, 1, QTableWidgetItem(user.username))
            self.user_table.setItem(row, 2, QTableWidgetItem(role_name))