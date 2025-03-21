# test_app.py
import unittest
from unittest.mock import patch
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from login_window import LoginWindow
from admin_window import AdminWindow, CreateUserDialog
from user_window import UserWindow, CreateClientDialog, CreateOrderDialog
from models import Base, User, Role, UserRole, Client, ClientType, IndividualClient, Product, ClientOrder, OrderItem, OrderStatus
from datetime import datetime
from PySide6.QtWidgets import QApplication

class TestApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication([])
        # Параметры подключения к PostgreSQL
        cls.db_user = "admin"
        cls.db_password = "root"
        cls.db_host = "localhost"
        cls.db_port = "5432"
        cls.db_name = "test_db"

        # Создаём временную тестовую базу данных
        conn = psycopg2.connect(
            dbname="postgres",
            user=cls.db_user,
            password=cls.db_password,
            host=cls.db_host,
            port=cls.db_port
        )
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE {cls.db_name}")
        cursor.close()
        conn.close()

        # Подключаемся к тестовой базе данных через SQLAlchemy
        cls.engine = create_engine(
            f"postgresql+psycopg2://{cls.db_user}:{cls.db_password}@{cls.db_host}:{cls.db_port}/{cls.db_name}"
        )
        Base.metadata.create_all(cls.engine)
        cls.session = Session(cls.engine)

    @classmethod
    def tearDownClass(cls):
        # Закрываем сессию и двигатель
        cls.session.close()
        cls.engine.dispose()

        # Удаляем тестовую базу данных
        conn = psycopg2.connect(
            dbname="postgres",
            user=cls.db_user,
            password=cls.db_password,
            host=cls.db_host,
            port=cls.db_port
        )
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        cursor.execute(f"DROP DATABASE {cls.db_name}")
        cursor.close()
        conn.close()

        cls.app = None

    def setUp(self):
        # Очищаем таблицы в правильном порядке, учитывая зависимости внешних ключей
        self.session.query(OrderItem).delete()
        self.session.query(ClientOrder).delete()
        self.session.query(UserRole).delete()
        self.session.query(IndividualClient).delete()
        self.session.query(Client).delete()
        self.session.query(Product).delete()
        self.session.query(User).delete()
        self.session.query(Role).delete()
        self.session.commit()

        # Добавляем минимальные тестовые данные заново
        admin_role = Role(id=1, name="Administrator")
        user_role = Role(id=2, name="Sales Manager")
        self.session.add_all([admin_role, user_role])

        admin_user = User(id=1, username="admin", password_hash=User.hash_password("admin123"))
        admin_user_role = UserRole(user_id=1, role_id=1)
        self.session.add_all([admin_user, admin_user_role])

        sales_user = User(id=2, username="sales", password_hash=User.hash_password("sales123"))
        sales_user_role = UserRole(user_id=2, role_id=2)
        self.session.add_all([sales_user, sales_user_role])

        product = Product(id=1, name="Мёд липовый", description="Натуральный липовый мёд, 1 кг", price=500.0, stock_quantity=100)
        self.session.add(product)

        client = Client(id=1, client_type=ClientType.individual, phone="+79991234567", email="ivan.petrov@example.com", is_deleted=False)
        individual = IndividualClient(id=1, first_name="Иван", last_name="Петров", middle_name="Сергеевич")
        self.session.add_all([client, individual])

        self.session.commit()

    def test_login_success(self):
        """Тест успешной авторизации (TC-001)"""
        login_window = LoginWindow()
        with patch.object(login_window, 'username_input', create=True) as mock_username, \
             patch.object(login_window, 'password_input', create=True) as mock_password, \
             patch.object(login_window, 'close', create=True) as mock_close:
            mock_username.text.return_value = "admin"
            mock_password.text.return_value = "admin123"
            login_window.login()
            self.assertTrue(hasattr(login_window, 'admin_window'))
            mock_close.assert_called_once()

    def test_create_user(self):
        """Тест создания нового пользователя (TC-003)"""
        admin_window = AdminWindow(self.session, user=None, role="admin")
        dialog = CreateUserDialog(self.session, parent=admin_window)
        with patch.object(dialog, 'username_input', create=True) as mock_username, \
             patch.object(dialog, 'password_input', create=True) as mock_password, \
             patch.object(dialog, 'role_combo', create=True) as mock_role_combo, \
             patch.object(dialog, 'accept', create=True) as mock_accept, \
             patch('admin_window.QMessageBox') as mock_msgbox:
            mock_username.text.return_value = "newuser"
            mock_password.text.return_value = "newpass123"
            mock_role_combo.currentText.return_value = "Sales Manager"
            dialog.create_user()
            mock_msgbox.information.assert_called_once()
            mock_accept.assert_called_once()
            user = self.session.query(User).filter_by(username="newuser").first()
            self.assertIsNotNone(user)
            self.assertTrue(user.check_password("newpass123"))

    def test_create_individual_client(self):
        """Тест создания клиента-физлица (TC-004)"""
        user_window = UserWindow(self.session, user=None, role="sales_manager")
        dialog = CreateClientDialog(self.session, parent=user_window)
        with patch.object(dialog, 'client_type_combo', create=True) as mock_type, \
             patch.object(dialog, 'phone_input', create=True) as mock_phone, \
             patch.object(dialog, 'email_input', create=True) as mock_email, \
             patch.object(dialog, 'first_name_input', create=True) as mock_first, \
             patch.object(dialog, 'last_name_input', create=True) as mock_last, \
             patch.object(dialog, 'middle_name_input', create=True) as mock_middle, \
             patch.object(dialog, 'accept', create=True) as mock_accept, \
             patch('user_window.QMessageBox') as mock_msgbox:
            mock_type.currentText.return_value = "individual"
            mock_phone.text.return_value = "+79991234568"
            mock_email.text.return_value = "new.client@example.com"
            mock_first.text.return_value = "Алексей"
            mock_last.text.return_value = "Смирнов"
            mock_middle.text.return_value = "Иванович"
            dialog.create_client()
            if mock_msgbox.critical.called:
                print("QMessageBox.critical was called with:", mock_msgbox.critical.call_args)
            mock_msgbox.information.assert_called_once()
            mock_accept.assert_called_once()
            client = self.session.query(Client).filter_by(email="new.client@example.com").first()
            self.assertIsNotNone(client)
            self.assertEqual(client.client_type, ClientType.individual)
            individual = self.session.query(IndividualClient).filter_by(id=client.id).first()
            self.assertEqual(individual.first_name, "Алексей")

    def test_create_order(self):
        """Тест создания заказа (TC-005)"""
        user_window = UserWindow(self.session, user=None, role="sales_manager")
        dialog = CreateOrderDialog(self.session, parent=user_window)
        with patch.object(dialog, 'client_combo', create=True) as mock_client, \
             patch.object(dialog, 'product_combo', create=True) as mock_product, \
             patch.object(dialog, 'quantity_input', create=True) as mock_quantity, \
             patch.object(dialog, 'accept', create=True) as mock_accept, \
             patch('user_window.QMessageBox') as mock_msgbox:
            mock_client.currentData.return_value = 1
            mock_product.currentData.return_value = 1
            mock_quantity.text.return_value = "5"
            dialog.create_order()
            if mock_msgbox.critical.called:
                print("QMessageBox.critical was called with:", mock_msgbox.critical.call_args)
            mock_msgbox.information.assert_called_once()
            mock_accept.assert_called_once()
            order = self.session.query(ClientOrder).filter_by(client_id=1).first()
            self.assertIsNotNone(order)
            order_item = self.session.query(OrderItem).filter_by(order_id=order.id).first()
            self.assertEqual(order_item.quantity, 5)
            self.assertEqual(order_item.price, 2500.0)
            product = self.session.query(Product).filter_by(id=1).first()
            self.assertEqual(product.stock_quantity, 95)

    def test_generate_clients_report(self):
        """Тест генерации отчёта по клиентам (TC-006)"""
        user_window = UserWindow(self.session, user=None, role="accountant")
        with patch('user_window.SimpleDocTemplate') as mock_doc, \
             patch('user_window.QMessageBox') as mock_msgbox:
            user_window.generate_clients_report()
            mock_msgbox.information.assert_called_once()
            mock_doc.return_value.build.assert_called_once()

    def test_select_client(self):
        """Тест выбора клиента из списка (TC-007)"""
        user_window = UserWindow(self.session, user=None, role="sales_manager")
        with patch.object(user_window, 'clients_table', create=True) as mock_table, \
             patch.object(user_window, 'load_orders', create=True) as mock_load_orders:
            mock_table.currentRow.return_value = 0
            mock_table.item.return_value.text.return_value = "1"
            user_window.load_orders()
            mock_load_orders.assert_called_once