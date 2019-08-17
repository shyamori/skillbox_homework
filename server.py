#  Created by Artem Manchenkov
#  artyom@manchenkoff.me
#
#  Copyright © 2019
#
#  Сервер для обработки сообщений от клиентов
#
from twisted.internet import reactor
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet.protocol import ServerFactory, connectionDone


class Client(LineOnlyReceiver):
    """Класс для обработки соединения с клиентом сервера"""

    delimiter = "\n".encode()  # \n для терминала, \r\n для GUI

    # указание фабрики для обработки подключений
    factory: 'Server'

    # информация о клиенте
    ip: str
    login: str = None

    def connectionMade(self):
        """
        Обработчик нового клиента

        - записать IP
        - внести в список клиентов
        - отправить сообщение приветствия
        """

        self.ip = self.transport.getPeer().host  # записываем IP адрес клиента
        self.factory.clients.append(self)  # добавляем в список клиентов фабрики

        self.sendLine("Welcome to the chat!".encode())  # отправляем сообщение клиенту

        print(f"Client {self.ip} connected")  # отображаем сообщение в консоли сервера

    def connectionLost(self, reason=connectionDone):
        """
        Обработчик закрытия соединения

        - удалить из списка клиентов
        - вывести сообщение в чат об отключении
        """

        self.factory.clients.remove(self)  # удаляем клиента из списка в фабрике

        print(f"Client {self.ip} disconnected")  # выводим уведомление в консоли сервера

    def lineReceived(self, line: bytes):
        """
        Обработчик нового сообщения от клиента

        - зарегистрировать, если это первый вход, уведомить чат
        - переслать сообщение в чат, если уже зарегистрирован
        """

        message = line.decode()  # раскодируем полученное сообщение в строку

        # если логин еще не зарегистрирован
        if self.login is None:
            if message.startswith("login:"):  # проверяем, чтобы в начале шел login:
                login = message.replace("login:", "")  # вырезаем часть после :

                """
                При попытке подключения клиента под логином, который уже есть в чате:
                - Отправлять клиенту текст с ошибкой "Логин {login} занят, попробуйте другой"
                - Отключать от сервера соединение клиента
                """

                for user in self.factory.clients:
                    if user.login == login:
                        login_error = f"Login {login} is already exist"
                        self.sendLine(login_error.encode())
                        print(login_error)

                        reactor.callLater(0.5, self.transport.loseConnection)
                        return

                else:
                    self.login = login
                    notification = f"New user: {self.login}"  # формируем уведомление о новом клиенте
                    print(notification)
                    self.factory.notify_all_users(notification)  # отсылаем всем в чат

                    self.sendHistory()

            else:
                self.sendLine("Invalid login".encode())  # шлем уведомление, если в сообщении ошибка
        # если логин уже есть и это следующее сообщение
        else:
            format_message = f"{self.login}: {message}"  # форматируем сообщение от имени клиента

            self.factory.messages.append(format_message)

            # отсылаем всем в чат и в консоль сервера
            self.factory.notify_all_users(format_message)
            print(format_message)

    def sendHistory(self):

        """
        При успешном подключении клиента в чат:
        - Отправляет ему последние 10 сообщений из чата
        """

        if len(self.factory.messages) > 0:
            for num_message in range(0, 10):
                self.sendLine((self.factory.messages[num_message]).encode())
                if num_message == len(self.factory.messages) - 1:
                    return
        else:
            self.sendLine("Here is empty for now".encode())


class Server(ServerFactory):
    """Класс для управления сервером"""

    clients: list  # список клиентов
    protocol = Client  # протокол обработки клиента

    def __init__(self):
        """
        Старт сервера

        - инициализация списка клиентов
        - вывод уведомления в консоль
        """

        self.clients = []  # создаем пустой список клиентов

        self.messages = [] # создаем пустой список сообщений

        print("Server started - OK")  # уведомление в консоль сервера

    def startFactory(self):
        """Запуск прослушивания клиентов (уведомление в консоль)"""

        print("Start listening ...")  # уведомление в консоль сервера

    def notify_all_users(self, message: str):
        """
        Отправка сообщения всем клиентам чата
        :param message: Текст сообщения
        """

        data = message.encode()  # закодируем текст в двоичное представление

        # отправим всем подключенным клиентам
        for user in self.clients:
            user.sendLine(data)


if __name__ == '__main__':
    # параметры прослушивания
    reactor.listenTCP(
        7410,
        Server()
    )

    # запускаем реактор
    reactor.run()
