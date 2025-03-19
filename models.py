from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, Date, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import enum
from sqlalchemy.exc import SQLAlchemyError
import bcrypt

# Определение базового класса для моделей
Base = declarative_base()

# Определение перечислений (enums)
class ClientType(enum.Enum):
    individual = "Физлицо"
    legal_entity = "Юрлицо"

class OrderStatus(enum.Enum):
    created = "Создан"
    awaiting_payment = "Ожидает оплаты"
    processing = "В обработке"
    awaiting_delivery = "Ожидает выдачи"
    completed = "Завершён"

class PaymentMethod(enum.Enum):
    cash = "Наличный"
    bank_transfer = "Безналичный"

# Модель для таблицы Role
class Role(Base):
    __tablename__ = "Role"
    id = Column(Integer, primary_key=True)
    name = Column(String(20), nullable=False)
    user_roles = relationship("UserRole", back_populates="role")

# Модель для таблицы User (убрали quantity и price)
class User(Base):
    __tablename__ = "User"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    user_roles = relationship("UserRole", back_populates="user")

    @staticmethod
    def hash_password(password: str) -> str:
        """Хеширует пароль с использованием bcrypt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """Проверяет, соответствует ли введённый пароль захешированному."""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

# Модель для таблицы UserRole
class UserRole(Base):
    __tablename__ = "UserRole"
    user_id = Column(Integer, ForeignKey("User.id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("Role.id"), primary_key=True)
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")

# Модель для таблицы Client
class Client(Base):
    __tablename__ = "Client"
    id = Column(Integer, primary_key=True)
    client_type = Column(Enum(ClientType), nullable=False)
    phone = Column(String(12))
    email = Column(String(50), unique=True)
    is_deleted = Column(Boolean, default=False)
    orders = relationship("ClientOrder", back_populates="client")
    individual_client = relationship("IndividualClient", uselist=False, back_populates="client")
    legal_entity_client = relationship("LegalEntityClient", uselist=False, back_populates="client")

# Модель для таблицы IndividualClient
class IndividualClient(Base):
    __tablename__ = "IndividualClient"
    id = Column(Integer, ForeignKey("Client.id"), primary_key=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    middle_name = Column(String(50))
    client = relationship("Client", back_populates="individual_client")

# Модель для таблицы LegalEntityClient
class LegalEntityClient(Base):
    __tablename__ = "LegalEntityClient"
    id = Column(Integer, ForeignKey("Client.id"), primary_key=True)
    company_name = Column(String(100))
    inn = Column(String(12))
    kpp = Column(String(9))
    ogrn = Column(String(15))
    client = relationship("Client", back_populates="legal_entity_client")

# Модель для таблицы ClientOrder
class ClientOrder(Base):
    __tablename__ = "ClientOrder"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("Client.id"))
    order_date = Column(Date)
    status = Column(Enum(OrderStatus), nullable=False)
    client = relationship("Client", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order")
    payment = relationship("Payment", uselist=False, back_populates="order")

# Модель для таблицы Product
class Product(Base):
    __tablename__ = "Product"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    description = Column(String(255))
    price = Column(Float)
    stock_quantity = Column(Integer)
    order_items = relationship("OrderItem", back_populates="product")

# Модель для таблицы OrderItem
class OrderItem(Base):
    __tablename__ = "OrderItem"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("ClientOrder.id"))
    product_id = Column(Integer, ForeignKey("Product.id"))
    quantity = Column(Integer)
    price = Column(Float)
    order = relationship("ClientOrder", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")

# Модель для таблицы Payment
class Payment(Base):
    __tablename__ = "Payment"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("ClientOrder.id"))
    amount = Column(Float)
    payment_date = Column(Date)
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    order = relationship("ClientOrder", back_populates="payment")

def create_connection():
    engine = create_engine("postgresql://admin:root@localhost:5432/med", echo = True) # Создаем объект Engine для подключения к базе данных
    Base.metadata.create_all(engine) # Создаем таблицу users в базе данных, если она еще не существует
    Session = sessionmaker(bind=engine) # Создаем фабрику сессий
    session = Session(bind = engine) # Создаем сессию для работы с базой данных
    return session