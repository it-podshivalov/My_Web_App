Шаги для запуска:

1. Запустите Docker

1. Убедитесь что порты 5432, 8000 не заняты, если заняты - освободите

2. В командной строке перейдите в директорию с проектом

3. Установите необходимые пакеты выполнив команду-
    pip install -r requirements.txt

4. Запустите приложение выполнив команду-
    uvicorn my_web_app:app --host 0.0.0.0


Описание работы:

При запуске приложения создается база данных postgres с 3-мя таблицами, которые автозаполняются следующими данными-
    -   в таблице stores создаются 5 магазинов
    -   в таблице items создаются 5 товарных позиций
    -   в таблице sales создаются 100 случайных записей продаж с случайной датой

GET-запрос на получение всех товарных позиций
    http://localhost:8000/items/

GET-запрос на получение всех магазинов
    http://localhost:8000/stores/

POST-запрос с json-телом для сохранения данных о произведенной продаже
    http://localhost:8000/sales/
    Пример тела запроса в json формате -
        {
            "item_id": 1,
            "store_id": 1
        }

GET-запрос на получение данных по топ 10 самых доходных магазинов за месяц
    http://localhost:8000/stores/top/

GET-запрос на получение данных по топ 10 самых продаваемых товаров
    http://localhost:8000/items/top/                