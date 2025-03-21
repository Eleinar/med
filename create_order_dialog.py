from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit, QMessageBox, QDialog
from PySide6.QtCore import Qt
from models import Client, ClientOrder, OrderItem, Product, OrderStatus, ClientType
from datetime import datetime

class CreateOrderDialog(QDialog):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.setWindowTitle("Создание нового заказа")
        self.setGeometry(200, 200, 400, 300)

        # Основной layout
        layout = QVBoxLayout()

        # Форма для создания заказа (вертикальное расположение)
        form_layout = QVBoxLayout()

        # Поле "Клиент"
        client_layout = QHBoxLayout()
        client_label = QLabel("Клиент:")
        self.client_combo = QComboBox(self)
        self.update_client_combo()
        client_layout.addWidget(client_label)
        client_layout.addWidget(self.client_combo)
        form_layout.addLayout(client_layout)

        # Поле "Товар"
        product_layout = QHBoxLayout()
        product_label = QLabel("Товар:")
        self.product_combo = QComboBox(self)
        self.update_product_combo()
        product_layout.addWidget(product_label)
        product_layout.addWidget(self.product_combo)
        form_layout.addLayout(product_layout)

        # Поле "Количество"
        quantity_layout = QHBoxLayout()
        quantity_label = QLabel("Количество:")
        self.quantity_input = QLineEdit(self)
        self.quantity_input.setPlaceholderText("Количество")
        quantity_layout.addWidget(quantity_label)
        quantity_layout.addWidget(self.quantity_input)
        form_layout.addLayout(quantity_layout)

        # Добавляем растяжку между полями и кнопкой
        form_layout.addStretch()

        layout.addLayout(form_layout)

        # Кнопка создания заказа
        self.create_button = QPushButton("Создать", self)
        self.create_button.clicked.connect(self.create_order)
        self.create_button.setFixedWidth(100)
        layout.addWidget(self.create_button, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    def update_client_combo(self):
        """Обновляет выпадающий список клиентов."""
        self.client_combo.clear()
        clients = self.session.query(Client).filter_by(is_deleted=False).all()
        for client in clients:
            # Определяем, что отображать: название организации или ФИО
            if client.client_type == ClientType.legal_entity and client.legal_entity_client:
                client_display = client.legal_entity_client.name
            elif client.client_type == ClientType.individual and client.individual_client:
                client_display = f"{client.individual_client.last_name} {client.individual_client.first_name}" + \
                                 (f" {client.individual_client.middle_name}" if client.individual_client.middle_name else "")
            else:
                client_display = "Неизвестный клиент"
            self.client_combo.addItem(f"{client.id} - {client_display}", client.id)

    def update_product_combo(self):
        """Обновляет выпадающий список товаров."""
        self.product_combo.clear()
        products = self.session.query(Product).all()
        for product in products:
            self.product_combo.addItem(f"{product.name} (Цена: {product.price})", product.id)

    def create_order(self):
        """Создаёт новый заказ."""
        try:
            client_id = self.client_combo.currentData()
            product_id = self.product_combo.currentData()
            quantity = self.quantity_input.text().strip()

            if not client_id or not product_id or not quantity:
                QMessageBox.warning(self, "Ошибка", "Заполните все поля")
                return

            quantity = int(quantity)
            if quantity <= 0:
                QMessageBox.warning(self, "Ошибка", "Количество должно быть больше 0")
                return

            product = self.session.query(Product).filter_by(id=product_id).first()
            if product.stock_quantity < quantity:
                QMessageBox.warning(self, "Ошибка", f"Недостаточно товара на складе. В наличии: {product.stock_quantity}")
                return

            # Создание заказа
            new_order = ClientOrder(
                client_id=client_id,
                order_date=datetime.now().date(),
                status=OrderStatus.created
            )
            self.session.add(new_order)
            self.session.flush()  # Получаем ID нового заказа

            # Создание позиции заказа
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=product_id,
                quantity=quantity,
                price=product.price * quantity
            )
            self.session.add(order_item)

            # Обновление остатка товара
            product.stock_quantity -= quantity

            self.session.commit()
            QMessageBox.information(self, "Успех", "Заказ успешно создан")
            self.accept()

        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Количество должно быть числом")
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании заказа: {e}")