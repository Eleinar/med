from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit, QMessageBox, QStackedWidget, QDialog
from sqlalchemy.orm import Session
from models import Client, ClientType, IndividualClient, LegalEntityClient

class CreateClientDialog(QDialog):
    def __init__(self, session: Session, parent=None):
        super().__init__(parent)
        self.session = session
        self.setWindowTitle("Создание нового клиента")
        self.setGeometry(200, 200, 500, 300)

        # Основной layout
        layout = QVBoxLayout()

        # Выбор типа клиента
        type_layout = QHBoxLayout()
        self.type_combo = QComboBox(self)
        self.type_combo.addItems(["Физлицо", "Юрлицо"])
        self.type_combo.currentTextChanged.connect(self.update_form)
        type_layout.addWidget(QLabel("Тип клиента:"))
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)

        # Общие поля для клиента
        common_layout = QHBoxLayout()
        self.phone_input = QLineEdit(self)
        self.phone_input.setPlaceholderText("Телефон")
        self.email_input = QLineEdit(self)
        self.email_input.setPlaceholderText("Email")
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
        self.first_name_input.setPlaceholderText("Имя")
        self.last_name_input = QLineEdit(self)
        self.last_name_input.setPlaceholderText("Фамилия")
        self.middle_name_input = QLineEdit(self)
        self.middle_name_input.setPlaceholderText("Отчество")
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
        self.company_name_input.setPlaceholderText("Название компании")
        self.inn_input = QLineEdit(self)
        self.inn_input.setPlaceholderText("ИНН")
        self.kpp_input = QLineEdit(self)
        self.kpp_input.setPlaceholderText("КПП")
        self.ogrn_input = QLineEdit(self)
        self.ogrn_input.setPlaceholderText("ОГРН")
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

        # Кнопка создания клиента
        self.create_button = QPushButton("Создать", self)
        self.create_button.clicked.connect(self.create_client)
        layout.addWidget(self.create_button)

        self.setLayout(layout)
        self.update_form()  # Инициализация формы

    def update_form(self):
        """Обновляет форму в зависимости от выбранного типа клиента."""
        if self.type_combo.currentText() == "Физлицо":
            self.form_stack.setCurrentIndex(0)
        else:
            self.form_stack.setCurrentIndex(1)

    def create_client(self):
        """Создаёт нового клиента."""
        try:
            phone = self.phone_input.text().strip() or None
            email = self.email_input.text().strip() or None
            client_type = ClientType.individual if self.type_combo.currentText() == "Физлицо" else ClientType.legal_entity

            if not email:
                QMessageBox.warning(self, "Ошибка", "Email обязателен")
                return

            # Проверка уникальности email
            if self.session.query(Client).filter_by(email=email).first():
                QMessageBox.warning(self, "Ошибка", "Клиент с таким email уже существует")
                return

            # Создание клиента
            new_client = Client(client_type=client_type, phone=phone, email=email, is_deleted=False)
            self.session.add(new_client)
            self.session.flush()  # Получаем ID нового клиента

            # Создание записи в зависимости от типа
            if client_type == ClientType.individual:
                first_name = self.first_name_input.text().strip() or None
                last_name = self.last_name_input.text().strip() or None
                middle_name = self.middle_name_input.text().strip() or None
                if not first_name or not last_name:
                    QMessageBox.warning(self, "Ошибка", "Имя и фамилия обязательны для физлица")
                    return
                individual_client = IndividualClient(
                    id=new_client.id,
                    first_name=first_name,
                    last_name=last_name,
                    middle_name=middle_name
                )
                self.session.add(individual_client)
            else:
                company_name = self.company_name_input.text().strip() or None
                inn = self.inn_input.text().strip() or None
                kpp = self.kpp_input.text().strip() or None
                ogrn = self.ogrn_input.text().strip() or None
                if not company_name or not inn:
                    QMessageBox.warning(self, "Ошибка", "Название компании и ИНН обязательны для юрлица")
                    return
                legal_entity_client = LegalEntityClient(
                    id=new_client.id,
                    company_name=company_name,
                    inn=inn,
                    kpp=kpp,
                    ogrn=ogrn
                )
                self.session.add(legal_entity_client)

            self.session.commit()
            QMessageBox.information(self, "Успех", "Клиент успешно создан")
            self.accept()  # Закрываем диалог

        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании клиента: {e}")