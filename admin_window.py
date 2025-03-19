from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QComboBox, QMessageBox
from sqlalchemy.orm import Session
from models import User, Role, UserRole
from sqlalchemy.exc import SQLAlchemyError

class AdminWindow(QMainWindow):
    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        self.setWindowTitle("Панель администратора - Управление пользователями")
        self.setGeometry(100, 100, 800, 600)

        # Центральный виджет и основной layout
        widget = QWidget()
        main_layout = QVBoxLayout()

        # Таблица для отображения пользователей
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(2)
        self.user_table.setHorizontalHeaderLabels(["ID", "Имя пользователя"])
        main_layout.addWidget(self.user_table)

        # Форма для добавления/редактирования пользователя
        user_form_layout = QHBoxLayout()
        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("Имя пользователя")
        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.role_combo = QComboBox(self)
        self.update_role_combo()  # Инициализация списка ролей
        user_form_layout.addWidget(QLabel("Имя:"))
        user_form_layout.addWidget(self.username_input)
        user_form_layout.addWidget(QLabel("Пароль:"))
        user_form_layout.addWidget(self.password_input)
        user_form_layout.addWidget(QLabel("Роль:"))
        user_form_layout.addWidget(self.role_combo)
        main_layout.addLayout(user_form_layout)

        # Форма для создания новой роли
        role_form_layout = QHBoxLayout()
        self.role_name_input = QLineEdit(self)
        self.role_name_input.setPlaceholderText("Название новой роли")
        self.create_role_button = QPushButton("Создать роль", self)
        self.create_role_button.clicked.connect(self.create_role)
        role_form_layout.addWidget(QLabel("Новая роль:"))
        role_form_layout.addWidget(self.role_name_input)
        role_form_layout.addWidget(self.create_role_button)
        main_layout.addLayout(role_form_layout)

        # Кнопки для управления пользователями
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Добавить", self)
        self.add_button.clicked.connect(self.add_user)
        self.edit_button = QPushButton("Редактировать", self)
        self.edit_button.clicked.connect(self.edit_user)
        self.delete_button = QPushButton("Удалить", self)
        self.delete_button.clicked.connect(self.delete_user)
        self.refresh_button = QPushButton("Обновить", self)
        self.refresh_button.clicked.connect(self.load_users)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.refresh_button)
        main_layout.addLayout(button_layout)

        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

        # Загрузка пользователей при старте
        self.load_users()

    def update_role_combo(self):
        """Обновляет выпадающий список ролей."""
        self.role_combo.clear()
        roles = self.session.query(Role).all()
        if roles:
            self.role_combo.addItems([role.name for role in roles])
        else:
            self.role_combo.addItem("Роли отсутствуют")

    def create_role(self):
        """Создаёт новую роль."""
        role_name = self.role_name_input.text().strip()
        if not role_name:
            QMessageBox.warning(self, "Ошибка", "Введите название роли")
            return

        # Проверка уникальности имени роли
        existing_role = self.session.query(Role).filter_by(name=role_name).first()
        if existing_role:
            QMessageBox.warning(self, "Ошибка", "Роль с таким названием уже существует")
            return

        # Добавление новой роли
        new_role = Role(name=role_name)
        self.session.add(new_role)
        self.session.commit()
        QMessageBox.information(self, "Успех", f"Роль '{role_name}' успешно создана")
        self.role_name_input.clear()
        self.update_role_combo()  # Обновляем список ролей

    def load_users(self):
        self.user_table.setRowCount(0)
        users = self.session.query(User).all()
        self.user_table.setRowCount(len(users))

        for row, user in enumerate(users):
            self.user_table.setItem(row, 0, QTableWidgetItem(str(user.id)))
            self.user_table.setItem(row, 1, QTableWidgetItem(user.username))

    def add_user(self):
        username = self.username_input.text()
        password = self.password_input.text()
        role_name = self.role_combo.currentText()
        role = self.session.query(Role).filter_by(name=role_name).first()

        if not role:
            QMessageBox.warning(self, "Ошибка", "Выберите существующую роль")
            return

        if username and password:
            password_hash = User.hash_password(password)  # Хешируем пароль
            new_user = User(username=username, password_hash=password_hash)
            self.session.add(new_user)
            self.session.flush()  # Получаем ID нового пользователя
            user_role = UserRole(user_id=new_user.id, role_id=role.id)
            self.session.add(user_role)
            self.session.commit()
            self.load_users()
            self.clear_user_inputs()

    def edit_user(self):
        selected_row = self.user_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя для редактирования")
            return
    
        try:
            user_id = int(self.user_table.item(selected_row, 0).text())
            user = self.session.query(User).filter_by(id=user_id).first()
            if not user:
                QMessageBox.warning(self, "Ошибка", "Пользователь не найден")
                return
    
            new_username = self.username_input.text().strip()
            if new_username and self.session.query(User).filter_by(username=new_username).exclude(id=user.id).first():
                QMessageBox.warning(self, "Ошибка", "Имя пользователя уже занято")
                return
    
            user.username = new_username or user.username
            if self.password_input.text():
                if len(self.password_input.text()) < 3:
                    QMessageBox.warning(self, "Ошибка", "Пароль должен содержать минимум 3 символа")
                    return
                user.password_hash = User.hash_password(self.password_input.text())
    
            role_name = self.role_combo.currentText()
            role = self.session.query(Role).filter_by(name=role_name).first()
            if role:
                user_role = self.session.query(UserRole).filter_by(user_id=user.id).first()
                if user_role:
                    user_role.role_id = role.id
                else:
                    user_role = UserRole(user_id=user.id, role_id=role.id)
                    self.session.add(user_role)
            else:
                QMessageBox.warning(self, "Ошибка", "Выберите существующую роль")
    
            self.session.commit()
            QMessageBox.information(self, "Успех", "Пользователь успешно отредактирован")
            self.load_users()
            self.clear_user_inputs()
    
        except SQLAlchemyError as e:
            self.session.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка базы данных: {e}")
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Некорректные данные")

    def delete_user(self):
        selected_row = self.user_table.currentRow()
        if selected_row >= 0:
            user_id = int(self.user_table.item(selected_row, 0).text())
            user = self.session.query(User).filter_by(id=user_id).first()
            if user:
                self.session.delete(user)  # Или можно использовать "мягкое удаление"
                self.session.commit()
                self.load_users()

    def clear_user_inputs(self):
        self.username_input.clear()
        self.password_input.clear()
        self.role_combo.setCurrentIndex(0)