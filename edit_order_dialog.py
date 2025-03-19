from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit, QMessageBox, QDialog
from sqlalchemy.orm import Session
from models import ClientOrder, OrderItem, Product, OrderStatus


class EditOrderDialog(QDialog):
    def __init__(self, session: Session, order: ClientOrder, parent=None):
        super().__init__(parent)
        self.session = session
        self.order = order
        self.order_item = self.session.query(OrderItem).filter_by(order_id=order.id).first()
        self.product = self.session.query(Product).filter_by(id=self.order_item.product_id).first()
        self.setWindowTitle("Редактирование заказа")
        self.setGeometry(200, 200, 400, 200)

        # Основной layout
        layout = QVBoxLayout()

        # Форма для редактирования заказа
        form_layout = QHBoxLayout()
        self.status_combo = QComboBox(self)
        self.status_combo.addItems([status.value for status in OrderStatus])
        self.status_combo.setCurrentText(order.status.value)
        self.quantity_input = QLineEdit(self)
        self.quantity_input.setText(str(self.order_item.quantity))
        form_layout.addWidget(QLabel("Статус:"))
        form_layout.addWidget(self.status_combo)
        form_layout.addWidget(QLabel("Количество:"))
        form_layout.addWidget(self.quantity_input)
        layout.addLayout(form_layout)

        # Кнопка сохранения
        self.save_button = QPushButton("Сохранить", self)
        self.save_button.clicked.connect(self.save_order)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def save_order(self):
        """Сохраняет изменения в заказе."""
        try:
            new_status = OrderStatus(self.status_combo.currentText())
            new_quantity = int(self.quantity_input.text().strip())

            if new_quantity <= 0:
                QMessageBox.warning(self, "Ошибка", "Количество должно быть больше 0")
                return

            # Проверка остатка товара
            original_quantity = self.order_item.quantity
            quantity_diff = new_quantity - original_quantity
            if quantity_diff > 0 and self.product.stock_quantity < quantity_diff:
                QMessageBox.warning(self, "Ошибка", f"Недостаточно товара на складе. В наличии: {self.product.stock_quantity}")
                return

            # Обновление заказа
            self.order.status = new_status
            self.order_item.quantity = new_quantity
            self.order_item.price = self.product.price * new_quantity
            self.product.stock_quantity -= quantity_diff

            self.session.commit()
            QMessageBox.information(self, "Успех", "Заказ успешно обновлён")
            self.accept()

        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Количество должно быть числом")
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении заказа: {e}")