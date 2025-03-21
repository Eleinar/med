from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit, QMessageBox, QDialog
from models import ClientOrder, OrderItem, Product, OrderStatus


class EditOrderDialog(QDialog):
    def __init__(self, session, order: ClientOrder, user_role: str, parent=None):
        super().__init__(parent)
        self.session = session
        self.order = order
        self.user_role = user_role
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

        # Ограничиваем доступ к полям в зависимости от роли
        if self.user_role in ["sales_manager", "director"]:
            # Менеджер по продажам и руководитель могут редактировать количество
            form_layout.addWidget(QLabel("Количество:"))
            form_layout.addWidget(self.quantity_input)
        if self.user_role in ["production_worker", "director"]:
            # Производственный сотрудник и руководитель могут менять статус
            form_layout.addWidget(QLabel("Статус:"))
            form_layout.addWidget(self.status_combo)

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
            new_quantity = int(self.quantity_input.text().strip()) if self.user_role in ["sales_manager", "director"] else self.order_item.quantity

            if new_quantity <= 0:
                QMessageBox.warning(self, "Ошибка", "Количество должно быть больше 0")
                return

            # Проверка остатка товара, если редактируется количество
            if self.user_role in ["sales_manager", "director"]:
                original_quantity = self.order_item.quantity
                quantity_diff = new_quantity - original_quantity
                if quantity_diff > 0 and self.product.stock_quantity < quantity_diff:
                    QMessageBox.warning(self, "Ошибка", f"Недостаточно товара на складе. В наличии: {self.product.stock_quantity}")
                    return
                self.order_item.quantity = new_quantity
                self.order_item.price = self.product.price * new_quantity
                self.product.stock_quantity -= quantity_diff

            # Обновление статуса, если разрешено
            if self.user_role in ["production_worker", "director"]:
                self.order.status = new_status

            self.session.commit()
            QMessageBox.information(self, "Успех", "Заказ успешно обновлён")
            self.accept()

        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Количество должно быть числом")
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении заказа: {e}")