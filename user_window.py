from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox, QStackedWidget
from sqlalchemy.orm import Session
from models import Client, ClientOrder, OrderItem, Product, ClientType
from datetime import datetime
from create_client_dialog import CreateClientDialog
from create_order_dialog import CreateOrderDialog
from edit_client_dialog import EditClientDialog
from edit_order_dialog import EditOrderDialog

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont('DejaVuSans', 'fonts/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'fonts/DejaVuSans-Bold.ttf'))

class UserWindow(QMainWindow):
    def __init__(self, session: Session, user, role: str):
        super().__init__()
        self.session = session
        self.user = user
        self.role = role
        self.setWindowTitle(f"Интерфейс пользователя - {self.role}")
        self.setGeometry(100, 100, 900, 600)

        # Центральный виджет и основной layout
        widget = QWidget()
        main_layout = QHBoxLayout()

        # Проверяем роль пользователя
        if self.role == "basic":
            # Базовый пользователь ничего не может
            layout = QVBoxLayout()
            layout.addWidget(QLabel("У вас нет доступа к функционалу. Обратитесь к администратору."))
            widget.setLayout(layout)
            self.setCentralWidget(widget)
            return

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

        sidebar_layout.addStretch()
        sidebar.setLayout(sidebar_layout)

        # Центральная область с QStackedWidget
        self.stacked_widget = QStackedWidget()
        self.client_page = QWidget()
        self.order_page = QWidget()

        # Страница "Клиенты"
        client_layout = QVBoxLayout()
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
        self.clients_report_button = QPushButton("Сформировать отчёт")
        self.clients_report_button.clicked.connect(self.generate_clients_report)

        # Ограничиваем доступ к кнопкам на странице "Клиенты"
        filter_layout.addWidget(self.all_clients_button)
        filter_layout.addWidget(self.individual_clients_button)
        filter_layout.addWidget(self.legal_entity_clients_button)
        if self.role == "director":
            # Руководитель может управлять клиентами
            filter_layout.addWidget(self.create_client_button)
            filter_layout.addWidget(self.edit_client_button)
            filter_layout.addWidget(self.delete_client_button)
        if self.role in ["accountant", "director"]:
            # Бухгалтер и руководитель могут формировать отчёты
            filter_layout.addWidget(self.clients_report_button)

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

        order_buttons_layout = QHBoxLayout()
        self.create_order_button = QPushButton("Создать заказ")
        self.create_order_button.clicked.connect(self.open_create_order_dialog)
        self.edit_order_button = QPushButton("Редактировать заказ")
        self.edit_order_button.clicked.connect(self.open_edit_order_dialog)
        self.orders_report_button = QPushButton("Сформировать отчёт")
        self.orders_report_button.clicked.connect(self.generate_orders_report)

        # Ограничиваем доступ к кнопкам на странице "Заказы"
        if self.role in ["sales_manager", "director"]:
            # Менеджер по продажам и руководитель могут создавать заказы
            order_buttons_layout.addWidget(self.create_order_button)
        if self.role in ["sales_manager", "production_worker", "director"]:
            # Менеджер, производственный сотрудник и руководитель могут редактировать заказы
            order_buttons_layout.addWidget(self.edit_order_button)
        if self.role in ["accountant", "director"]:
            # Бухгалтер и руководитель могут формировать отчёты
            order_buttons_layout.addWidget(self.orders_report_button)

        order_layout.addLayout(order_buttons_layout)
        order_layout.addWidget(self.order_table)
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
        self.stacked_widget.setCurrentIndex(0)

    def open_create_client_dialog(self):
        dialog = CreateClientDialog(self.session, self)
        if dialog.exec():
            self.load_clients()

    def open_edit_client_dialog(self):
        selected_row = self.client_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите клиента для редактирования")
            return
        client_id = int(self.client_table.item(selected_row, 0).text())
        client = self.session.query(Client).filter_by(id=client_id).first()
        if client:
            dialog = EditClientDialog(self.session, client, self)
            if dialog.exec():
                self.load_clients()

    def delete_client(self):
        selected_row = self.client_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите клиента для удаления")
            return

        client_id = int(self.client_table.item(selected_row, 0).text())
        client = self.session.query(Client).filter_by(id=client_id).first()
        if not client:
            QMessageBox.warning(self, "Ошибка", "Клиент не найден")
            return

        reply = QMessageBox.question(self, "Подтверждение", f"Вы уверены, что хотите удалить клиента {client.email}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                client.is_deleted = True
                self.session.commit()
                QMessageBox.information(self, "Успех", "Клиент успешно удалён")
                self.load_clients()
                self.order_table.setRowCount(0)
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении клиента: {e}")

    def open_create_order_dialog(self):
        dialog = CreateOrderDialog(self.session, self)
        if dialog.exec():
            self.load_orders()

    def open_edit_order_dialog(self):
        selected_row = self.order_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите заказ для редактирования")
            return
        order_id = int(self.order_table.item(selected_row, 0).text())
        order = self.session.query(ClientOrder).filter_by(id=order_id).first()
        if order:
            dialog = EditOrderDialog(self.session, order, self.role, self)
            if dialog.exec():
                self.load_orders()

    def generate_clients_report(self):
        try:
            current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"clients_report_{current_date}.pdf"
            doc = SimpleDocTemplate(filename, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()

            # Определяем стили с использованием шрифта DejaVuSans
            styles.add(ParagraphStyle(name='MyTitle', fontName='DejaVuSans-Bold', fontSize=14, leading=16, alignment=1))
            styles.add(ParagraphStyle(name='MyNormal', fontName='DejaVuSans', fontSize=10, leading=12))
            styles.add(ParagraphStyle(name='TableCell', fontName='DejaVuSans', fontSize=8, leading=10, alignment=1))

            elements.append(Paragraph("Отчёт по клиентам", styles['MyTitle']))
            elements.append(Paragraph(f"Дата формирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['MyNormal']))
            elements.append(Paragraph("<br/><br/>", styles['MyNormal']))

            # Заголовки таблицы
            data = [["ID", "Тип клиента", "Телефон", "Email", "ИНН", "ОГРН", "КПП"]]
            clients = self.session.query(Client).filter_by(is_deleted=False).all()

            # Преобразуем данные в Paragraph для переноса текста
            for client in clients:
                row = [
                    Paragraph(str(client.id), styles['TableCell']),
                    Paragraph(client.client_type.value, styles['TableCell']),
                    Paragraph(client.phone or "", styles['TableCell']),
                    Paragraph(client.email or "", styles['TableCell']),
                    Paragraph(client.legal_entity_client.inn if client.client_type == ClientType.legal_entity and client.legal_entity_client else "", styles['TableCell']),
                    Paragraph(client.legal_entity_client.ogrn if client.client_type == ClientType.legal_entity and client.legal_entity_client else "", styles['TableCell']),
                    Paragraph(client.legal_entity_client.kpp if client.client_type == ClientType.legal_entity and client.legal_entity_client else "", styles['TableCell'])
                ]
                data.append(row)

            # Указываем ширину столбцов (сумма должна быть около 540 пунктов для A4)
            col_widths = [40, 80, 80, 120, 80, 80, 50]  # Подобраны экспериментально
            table = Table(data, colWidths=col_widths)

            # Настраиваем стиль таблицы
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSans-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'DejaVuSans'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(table)

            doc.build(elements)
            QMessageBox.information(self, "Успех", f"Отчёт успешно сформирован: {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при формировании отчёта: {e}")

    def generate_orders_report(self):
        try:
            current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"orders_report_{current_date}.pdf"
            doc = SimpleDocTemplate(filename, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()

            # Определяем стили с использованием шрифта DejaVuSans
            styles.add(ParagraphStyle(name='MyTitle', fontName='DejaVuSans-Bold', fontSize=14, leading=16, alignment=1))
            styles.add(ParagraphStyle(name='MyNormal', fontName='DejaVuSans', fontSize=10, leading=12))
            styles.add(ParagraphStyle(name='TableCell', fontName='DejaVuSans', fontSize=8, leading=10, alignment=1))

            elements.append(Paragraph("Отчёт по заказам", styles['MyTitle']))
            elements.append(Paragraph(f"Дата формирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['MyNormal']))
            elements.append(Paragraph("<br/><br/>", styles['MyNormal']))

            selected_row = self.client_table.currentRow()
            if selected_row >= 0:
                client_id = int(self.client_table.item(selected_row, 0).text())
                client = self.session.query(Client).filter_by(id=client_id).first()
                # Отображаем название организации или ФИО в заголовке отчёта
                if client.client_type == ClientType.legal_entity and client.legal_entity_client:
                    client_display = client.legal_entity_client.name
                elif client.client_type == ClientType.individual and client.individual_client:
                    client_display = f"{client.individual_client.last_name} {client.individual_client.first_name}" + \
                                     (f" {client.individual_client.middle_name}" if client.individual_client.middle_name else "")
                else:
                    client_display = "Неизвестный клиент"
                elements.append(Paragraph(f"Клиент: {client_display}", styles['MyNormal']))
                orders = self.session.query(ClientOrder).filter_by(client_id=client_id).all()
            else:
                elements.append(Paragraph("Все заказы", styles['MyNormal']))
                orders = self.session.query(ClientOrder).all()

            # Заголовки таблицы
            data = [["ID", "Дата заказа", "Статус", "Клиент", "Товар", "Количество", "Цена"]]
            for order in orders:
                order_item = self.session.query(OrderItem).filter_by(order_id=order.id).first()
                if order_item:
                    product = self.session.query(Product).filter_by(id=order_item.product_id).first()
                    # Получаем клиента по client_id
                    client = self.session.query(Client).filter_by(id=order.client_id).first()
                    # Определяем, что отображать: название организации или ФИО
                    if client:
                        if client.client_type == ClientType.legal_entity and client.legal_entity_client:
                            client_display = client.legal_entity_client.name
                        elif client.client_type == ClientType.individual and client.individual_client:
                            client_display = f"{client.individual_client.last_name} {client.individual_client.first_name}" + \
                                             (f" {client.individual_client.middle_name}" if client.individual_client.middle_name else "")
                        else:
                            client_display = "Неизвестный клиент"
                    else:
                        client_display = "Неизвестный клиент"
                    row = [
                        Paragraph(str(order.id), styles['TableCell']),
                        Paragraph(str(order.order_date) if order.order_date else "", styles['TableCell']),
                        Paragraph(order.status.value, styles['TableCell']),
                        Paragraph(client_display, styles['TableCell']),
                        Paragraph(product.name if product else "", styles['TableCell']),
                        Paragraph(str(order_item.quantity), styles['TableCell']),
                        Paragraph(str(order_item.price), styles['TableCell'])
                    ]
                    data.append(row)

            # Указываем ширину столбцов (сумма должна быть около 540 пунктов для A4)
            col_widths = [40, 100, 60, 60, 120, 60, 80]  # Подобраны экспериментально
            table = Table(data, colWidths=col_widths)

            # Настраиваем стиль таблицы
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSans-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'DejaVuSans'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(table)

            doc.build(elements)
            QMessageBox.information(self, "Успех", f"Отчёт успешно сформирован: {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при формировании отчёта: {e}")

    def load_clients(self, client_type=None):
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
            if client.client_type == ClientType.legal_entity and client.legal_entity_client:
                self.client_table.setItem(row, 4, QTableWidgetItem(client.legal_entity_client.inn or ""))
                self.client_table.setItem(row, 5, QTableWidgetItem(client.legal_entity_client.ogrn or ""))
                self.client_table.setItem(row, 6, QTableWidgetItem(client.legal_entity_client.kpp or ""))
            else:
                self.client_table.setItem(row, 4, QTableWidgetItem(""))
                self.client_table.setItem(row, 5, QTableWidgetItem(""))
                self.client_table.setItem(row, 6, QTableWidgetItem(""))

    def load_orders(self):
        selected_row = self.client_table.currentRow()
        if selected_row >= 0:
            client_id = int(self.client_table.item(selected_row, 0).text())
            self.order_table.setRowCount(0)
            orders = self.session.query(ClientOrder).filter_by(client_id=client_id).all()
            self.order_table.setRowCount(len(orders))
            for row, order in enumerate(orders):
                # Получаем клиента по client_id
                client = self.session.query(Client).filter_by(id=order.client_id).first()
                # Определяем, что отображать: название организации или ФИО
                if client:
                    if client.client_type == ClientType.legal_entity and client.legal_entity_client:
                        client_display = client.legal_entity_client.name
                    elif client.client_type == ClientType.individual and client.individual_client:
                        client_display = f"{client.individual_client.last_name} {client.individual_client.first_name}" + \
                                         (f" {client.individual_client.middle_name}" if client.individual_client.middle_name else "")
                    else:
                        client_display = "Неизвестный клиент"
                else:
                    client_display = "Неизвестный клиент"
                self.order_table.setItem(row, 0, QTableWidgetItem(str(order.id)))
                self.order_table.setItem(row, 1, QTableWidgetItem(str(order.order_date) if order.order_date else ""))
                self.order_table.setItem(row, 2, QTableWidgetItem(order.status.value))
                self.order_table.setItem(row, 3, QTableWidgetItem(client_display))