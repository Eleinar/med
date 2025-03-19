from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QComboBox, QLineEdit, QMessageBox, QStackedWidget, QDialog
from PySide6.QtCore import Qt
from sqlalchemy.orm import Session
from models import Client, ClientOrder, OrderItem, Product, OrderStatus, ClientType, IndividualClient, LegalEntityClient
from datetime import datetime
from create_client_dialog import CreateClientDialog
from create_order_dialog import CreateOrderDialog
from edit_client_dialog import EditClientDialog
from edit_order_dialog import EditOrderDialog

class UserWindow(QMainWindow):
    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        self.setWindowTitle("Интерфейс пользователя - Работа с клиентами и заказами")
        self.setGeometry(100, 100, 900, 600)

        # Центральный виджет и основной layout
        widget = QWidget()
        main_layout = QHBoxLayout()

        # Боковая панель (sidebar)
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout()
        sidebar.setFixedWidth(150)

        self.clients_button = QPushButton("Клиенты")
        self.clients_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        sidebar_layout.addWidget(self.clients_button)

        self.orders_button = QPushButton("Заказы")
        self.orders_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        sidebar_layout.addWidget(self.orders_button)

        sidebar_layout.addStretch()  # Заполнение оставшегося пространства
        sidebar.setLayout(sidebar_layout)

        # Центральная область с QStackedWidget
        self.stacked_widget = QStackedWidget()
        self.client_page = QWidget()
        self.order_page = QWidget()

        # Страница "Клиенты"
        client_layout = QVBoxLayout()
        # Кнопки фильтрации и управления клиентами
        filter_layout = QHBoxLayout()
        self.all_clients_button = QPushButton("Все клиенты")
        self.all_clients_button.clicked.connect(lambda: self.load_clients(client_type=None))
        self.individual_clients_button = QPushButton("Физические лица")
        self.individual_clients_button.clicked.connect(lambda: self.load_clients(client_type=ClientType.individual))
        self.legal_entity_clients_button = QPushButton("Юридические лица")
        self.legal_entity_clients_button.clicked.connect(lambda: self.load_clients(client_type=ClientType.legal_entity))
        self.create_client_button = QPushButton("Создать клиента")
        self.create_client_button.clicked.connect(self.open_create_client_dialog)
        self.edit_client_button = QPushButton("Редактировать клиента")
        self.edit_client_button.clicked.connect(self.open_edit_client_dialog)
        self.delete_client_button = QPushButton("Удалить клиента")
        self.delete_client_button.clicked.connect(self.delete_client)
        filter_layout.addWidget(self.all_clients_button)
        filter_layout.addWidget(self.individual_clients_button)
        filter_layout.addWidget(self.legal_entity_clients_button)
        filter_layout.addWidget(self.create_client_button)
        filter_layout.addWidget(self.edit_client_button)
        filter_layout.addWidget(self.delete_client_button)
        client_layout.addLayout(filter_layout)

        self.client_table = QTableWidget()
        self.client_table.setColumnCount(7)
        self.client_table.setHorizontalHeaderLabels(["ID", "Тип клиента", "Телефон", "Email", "ИНН", "ОГРН", "КПП"])
        self.client_table.clicked.connect(self.load_orders)
        client_layout.addWidget(self.client_table)
        self.client_page.setLayout(client_layout)

        # Страница "Заказы"
        order_layout = QVBoxLayout()
        self.order_table = QTableWidget()
        self.order_table.setColumnCount(4)
        self.order_table.setHorizontalHeaderLabels(["ID", "Дата заказа", "Статус", "Клиент"])
        order_layout.addWidget(self.order_table)
        # Кнопки для управления заказами
        order_buttons_layout = QHBoxLayout()
        self.create_order_button = QPushButton("Создать заказ", self)
        self.create_order_button.clicked.connect(self.open_create_order_dialog)
        self.edit_order_button = QPushButton("Редактировать заказ", self)
        self.edit_order_button.clicked.connect(self.open_edit_order_dialog)
        order_buttons_layout.addWidget(self.create_order_button)
        order_buttons_layout.addWidget(self.edit_order_button)
        order_layout.addLayout(order_buttons_layout)
        self.order_page.setLayout(order_layout)

        # Добавление страниц в QStackedWidget
        self.stacked_widget.addWidget(self.client_page)
        self.stacked_widget.addWidget(self.order_page)

        # Сборка основного layout
        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.stacked_widget)
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

        # Загрузка клиентов при старте
        self.load_clients()
        self.stacked_widget.setCurrentIndex(0)  # По умолчанию открываем "Клиенты"

    def open_create_client_dialog(self):
        """Открывает диалоговое окно для создания клиента."""
        dialog = CreateClientDialog(self.session, self)
        if dialog.exec():
            self.load_clients()  # Обновляем таблицу клиентов после создания

    def open_edit_client_dialog(self):
        """Открывает диалоговое окно для редактирования клиента."""
        selected_row = self.client_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите клиента для редактирования")
            return
        client_id = int(self.client_table.item(selected_row, 0).text())
        client = self.session.query(Client).filter_by(id=client_id).first()
        if client:
            dialog = EditClientDialog(self.session, client, self)
            if dialog.exec():
                self.load_clients()  # Обновляем таблицу клиентов после редактирования

    def open_create_order_dialog(self):
        """Открывает диалоговое окно для создания заказа."""
        dialog = CreateOrderDialog(self.session, self)
        if dialog.exec():
            self.load_orders()  # Обновляем таблицу заказов после создания

    def open_edit_order_dialog(self):
        """Открывает диалоговое окно для редактирования заказа."""
        selected_row = self.order_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите заказ для редактирования")
            return
        order_id = int(self.order_table.item(selected_row, 0).text())
        order = self.session.query(ClientOrder).filter_by(id=order_id).first()
        if order:
            dialog = EditOrderDialog(self.session, order, self)
            if dialog.exec():
                self.load_orders()  # Обновляем таблицу заказов после редактирования
                
    def delete_client(self):
        """Удаляет клиента (мягкое удаление)."""
        selected_row = self.client_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите клиента для удаления")
            return
    
        client_id = int(self.client_table.item(selected_row, 0).text())
        client = self.session.query(Client).filter_by(id=client_id).first()
        if not client:
            QMessageBox.warning(self, "Ошибка", "Клиент не найден")
            return

        # Подтверждение удаления
        reply = QMessageBox.question(self, "Подтверждение", f"Вы уверены, что хотите удалить клиента {client.email}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                client.is_deleted = True
                self.session.commit()
                QMessageBox.information(self, "Успех", "Клиент успешно удалён")
                self.load_clients()  # Обновляем таблицу клиентов
                self.order_table.setRowCount(0)  # Очищаем таблицу заказов
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении клиента: {e}")

    def load_clients(self, client_type=None):
        """Загружает список клиентов с возможностью фильтрации по типу."""
        self.client_table.setRowCount(0)
        query = self.session.query(Client).filter_by(is_deleted=False)
        if client_type:
            query = query.filter_by(client_type=client_type)
        clients = query.all()
        self.client_table.setRowCount(len(clients))
        for row, client in enumerate(clients):
            self.client_table.setItem(row, 0, QTableWidgetItem(str(client.id)))
            self.client_table.setItem(row, 1, QTableWidgetItem(client.client_type.value))
            self.client_table.setItem(row, 2, QTableWidgetItem(client.phone or ""))
            self.client_table.setItem(row, 3, QTableWidgetItem(client.email or ""))
            
            # Добавляем данные для юрлиц
            if client.client_type == ClientType.legal_entity and client.legal_entity_client:
                self.client_table.setItem(row, 4, QTableWidgetItem(client.legal_entity_client.inn or ""))
                self.client_table.setItem(row, 5, QTableWidgetItem(client.legal_entity_client.ogrn or ""))
                self.client_table.setItem(row, 6, QTableWidgetItem(client.legal_entity_client.kpp or ""))
            else:
                self.client_table.setItem(row, 4, QTableWidgetItem(""))
                self.client_table.setItem(row, 5, QTableWidgetItem(""))
                self.client_table.setItem(row, 6, QTableWidgetItem(""))

    def load_orders(self):
        """Загружает заказы для выбранного клиента."""
        selected_row = self.client_table.currentRow()
        if selected_row >= 0:
            client_id = int(self.client_table.item(selected_row, 0).text())
            self.order_table.setRowCount(0)
            orders = self.session.query(ClientOrder).filter_by(client_id=client_id).all()
            self.order_table.setRowCount(len(orders))
            for row, order in enumerate(orders):
                self.order_table.setItem(row, 0, QTableWidgetItem(str(order.id)))
                self.order_table.setItem(row, 1, QTableWidgetItem(str(order.order_date) if order.order_date else ""))
                self.order_table.setItem(row, 2, QTableWidgetItem(order.status.value))
                self.order_table.setItem(row, 3, QTableWidgetItem(str(order.client_id)))