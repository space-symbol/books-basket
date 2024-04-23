import sys
from decimal import Decimal
from PyQt5.QtWidgets import QLabel, QApplication, QWidget, QVBoxLayout, QGroupBox, QPushButton, QCheckBox, QMessageBox
import pymysql


class FoodShopApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Baby Food Shop")
        self.setGeometry(100, 100, 400, 300)
        self.initUI()

    def connect_to_database(self):
        self.connection = pymysql.connect(
            host='localhost',
            user='admin',
            password='ePPXyiUis-2309',
            db='baby_food_shop',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

    def initUI(self):
        layout = QVBoxLayout()

        # Создание группы с флажками
        self.food_group_box = QGroupBox("Выберите продукты:")
        self.food_layout = QVBoxLayout()
        self.food_group_box.setLayout(self.food_layout)
        layout.addWidget(self.food_group_box)

        self.connect_to_database()
        # Получение списка еды из базы данных и добавление флажков
        self.populate_food_checkboxes()

        # Кнопка добавления в корзину
        self.add_to_basket_button = QPushButton("Добавить в корзину")
        self.clear_basket_button = QPushButton("Очистить корзину")
        self.show_basket_button = QPushButton('Показать корзину')
        self.add_to_basket_button.clicked.connect(self.add_to_basket)
        self.clear_basket_button.clicked.connect(self.clear_basket)
        self.show_basket_button.clicked.connect(self.show_basket_dialog)
        layout.addWidget(self.add_to_basket_button)
        layout.addWidget(self.clear_basket_button)
        layout.addWidget(self.show_basket_button)
        self.setLayout(layout)

    def populate_food_checkboxes(self):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT * FROM types")
                types = cursor.fetchall()
                for food_type in types:
                    type_name = food_type['name']
                    cursor.callproc('GetFoodWithType', (type_name,))
                    foods = cursor.fetchall()
                    group_label = QLabel(type_name)
                    self.food_layout.addWidget(group_label)
                    for food in foods:
                        print(food)
                        checkbox = QCheckBox(food['name'] + f" ({food['price']} руб.)")
                        checkbox.food_id = food['id']
                        self.food_layout.addWidget(checkbox)
        except Exception as err:
            print(err)
        finally:
            cursor.close()

    def add_to_basket(self):
        try:
            with self.connection.cursor() as cursor:
                for i in range(self.food_layout.count()):
                    widget = self.food_layout.itemAt(i).widget()
                    if isinstance(widget, QCheckBox) and widget.isChecked():
                        cursor.callproc('AddFoodInBasket', (widget.text().split(' (')[0],))
                        self.connection.commit()
                cursor.callproc('GetBasketFood')
                basket_items = cursor.fetchall()
                if basket_items:
                    self.show_basket_dialog()
                else:
                    QMessageBox.information(self, "Корзина", "Нет товаров в корзине", QMessageBox.Ok)
        except Exception as err:
            print(err)

    def clear_basket(self):
        try:
            cursor = self.connection.cursor()
            cursor.execute("TRUNCATE BASKET")
            self.connection.commit()
            self.show_basket_dialog()
        except Exception as err:
            print(err)

    def show_basket_dialog(self):
        cursor = self.connection.cursor()
        cursor.callproc('GetBasketFood')
        basket_items = cursor.fetchall()
        message = "Товары в корзине:\n"

        for item in basket_items:
            message += f"{item['food_name']} {item['type_name']} ({item['amount']})\n"
            print(item)

        total_price = Decimal(0)

        for item in basket_items:
            total_price += item['price']

        message += f"\nК оплате {total_price} руб."
        QMessageBox.information(self, "Корзина", message, QMessageBox.Ok)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FoodShopApp()
    window.show()
    sys.exit(app.exec_())
