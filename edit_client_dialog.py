from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QMessageBox, QStackedWidget, QDialog

from models import Client, ClientType


class EditClientDialog(QDialog):
    def __init__(self, session, client: Client, parent=None):
        super().__init__(parent)
        self.session = session
        self.client = client
        self.setWindowTitle("Редактирование клиента")
        self.setGeometry(200, 200, 500, 300)

        # Основной layout
        layout = QVBoxLayout()

        # Общие поля для клиента
        common_layout = QHBoxLayout()
        self.phone_input = QLineEdit(self)
        self.phone_input.setText(client.phone or "")
        self.email_input = QLineEdit(self)
        self.email_input.setText(client.email or "")
        common_layout.addWidget(QLabel("Телефон:"))
        common_layout.addWidget(self.phone_input)
        common_layout.addWidget(QLabel("Email:"))
        common_layout.addWidget(self.email_input)
        layout.addLayout(common_layout)

        # QStackedWidget для переключения форм
        self.form_stack = QStackedWidget()

        # Форма для физлица
        self.individual_form = QWidget()
        individual_layout = QVBoxLayout()
        self.first_name_input = QLineEdit(self)
        self.first_name_input.setText(client.individual_client.first_name if client.individual_client else "")
        self.last_name_input = QLineEdit(self)
        self.last_name_input.setText(client.individual_client.last_name if client.individual_client else "")
        self.middle_name_input = QLineEdit(self)
        self.middle_name_input.setText(client.individual_client.middle_name if client.individual_client else "")
        individual_layout.addWidget(QLabel("Имя:"))
        individual_layout.addWidget(self.first_name_input)
        individual_layout.addWidget(QLabel("Фамилия:"))
        individual_layout.addWidget(self.last_name_input)
        individual_layout.addWidget(QLabel("Отчество:"))
        individual_layout.addWidget(self.middle_name_input)
        self.individual_form.setLayout(individual_layout)

        # Форма для юрлица
        self.legal_entity_form = QWidget()
        legal_entity_layout = QVBoxLayout()
        self.company_name_input = QLineEdit(self)
        self.company_name_input.setText(client.legal_entity_client.company_name if client.legal_entity_client else "")
        self.inn_input = QLineEdit(self)
        self.inn_input.setText(client.legal_entity_client.inn if client.legal_entity_client else "")
        self.kpp_input = QLineEdit(self)
        self.kpp_input.setText(client.legal_entity_client.kpp if client.legal_entity_client else "")
        self.ogrn_input = QLineEdit(self)
        self.ogrn_input.setText(client.legal_entity_client.ogrn if client.legal_entity_client else "")
        legal_entity_layout.addWidget(QLabel("Название компании:"))
        legal_entity_layout.addWidget(self.company_name_input)
        legal_entity_layout.addWidget(QLabel("ИНН:"))
        legal_entity_layout.addWidget(self.inn_input)
        legal_entity_layout.addWidget(QLabel("КПП:"))
        legal_entity_layout.addWidget(self.kpp_input)
        legal_entity_layout.addWidget(QLabel("ОГРН:"))
        legal_entity_layout.addWidget(self.ogrn_input)
        self.legal_entity_form.setLayout(legal_entity_layout)

        # Добавление форм в QStackedWidget
        self.form_stack.addWidget(self.individual_form)
        self.form_stack.addWidget(self.legal_entity_form)
        layout.addWidget(self.form_stack)

        # Кнопка сохранения
        self.save_button = QPushButton("Сохранить", self)
        self.save_button.clicked.connect(self.save_client)
        layout.addWidget(self.save_button)

        self.setLayout(layout)
        self.update_form()

    def update_form(self):
        """Обновляет форму в зависимости от типа клиента."""
        if self.client.client_type == ClientType.individual:
            self.form_stack.setCurrentIndex(0)
        else:
            self.form_stack.setCurrentIndex(1)

    def save_client(self):
        """Сохраняет изменения в клиенте."""
        try:
            new_phone = self.phone_input.text().strip() or None
            new_email = self.email_input.text().strip() or None

            if not new_email:
                QMessageBox.warning(self, "Ошибка", "Email обязателен")
                return

            # Проверка уникальности email
            existing_client = self.session.query(Client).filter_by(email=new_email).filter(Client.id != self.client.id).first()
            if existing_client:
                QMessageBox.warning(self, "Ошибка", "Клиент с таким email уже существует")
                return

            # Обновление общих полей
            self.client.phone = new_phone
            self.client.email = new_email

            # Обновление специфических полей
            if self.client.client_type == ClientType.individual:
                first_name = self.first_name_input.text().strip() or None
                last_name = self.last_name_input.text().strip() or None
                middle_name = self.middle_name_input.text().strip() or None
                if not first_name or not last_name:
                    QMessageBox.warning(self, "Ошибка", "Имя и фамилия обязательны для физлица")
                    return
                if self.client.individual_client:
                    self.client.individual_client.first_name = first_name
                    self.client.individual_client.last_name = last_name
                    self.client.individual_client.middle_name = middle_name
            else:
                company_name = self.company_name_input.text().strip() or None
                inn = self.inn_input.text().strip() or None
                kpp = self.kpp_input.text().strip() or None
                ogrn = self.ogrn_input.text().strip() or None
                if not company_name or not inn:
                    QMessageBox.warning(self, "Ошибка", "Название компании и ИНН обязательны для юрлица")
                    return
                if self.client.legal_entity_client:
                    self.client.legal_entity_client.company_name = company_name
                    self.client.legal_entity_client.inn = inn
                    self.client.legal_entity_client.kpp = kpp
                    self.client.legal_entity_client.ogrn = ogrn

            self.session.commit()
            QMessageBox.information(self, "Успех", "Клиент успешно обновлён")
            self.accept()

        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении клиента: {e}")