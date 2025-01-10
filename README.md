# api_final

## Описание

Данный проект является RESTful API, предназначенным для управления блогами, постами и комментариями. Он реализован с использованием Django и Django REST Framework, предоставляя возможности для создания, чтения, обновления и удаления постов и комментариев. Кроме того, проект включает управление сообществами и подписками пользователей, а также поддержку аутентификации с помощью JWT (JSON Web Tokens), что обеспечивает безопасность и контроль доступа к ресурсам API.


### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/daniil-pozdeev/api_final_yatube.git
```

```
cd kittygram
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

```
source env/bin/activate
```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate
```

Запустить проект:

```
python manage.py runserver
```

Убедитесь, что у вас установлен PostgreSQL или используйте SQLite для простоты.


Создайте суперпользователя (для доступа к админке):
   ```
   python manage.py createsuperuser
   ```


Теперь вы можете получить доступ к API по адресу `http://localhost:8000/`.

## Примеры

### Получение списка публикаций

Для получения списка всех публикаций отправьте GET-запрос на `/api/v1/posts/`:

```bash
curl -H "Authorization: Bearer <ваш_access_token>" http://localhost:8000/api/v1/posts/
```

**Ответ (200 OK)**:
```json
{
    "count": 123,
    "next": "http://localhost:8000/api/v1/posts/?offset=10&limit=10",
    "previous": null,
    "results": [
        {
            "id": 1,
            "author": "username",
            "text": "Текст публикации",
            "pub_date": "2019-08-24T14:15:22Z",
            "image": null,
            "group": null
        }
    ]
}
```

### Создание новой публикации

Отправьте POST-запрос на `/api/v1/posts/` с данными новой публикации:

```bash
curl -X POST -H "Authorization: Bearer <ваш_access_token>" -H "Content-Type: application/json" -d '{
    "text": "Текст новой публикации",
    "image": null,
    "group": null
}' http://localhost:8000/api/v1/posts/
```

**Ответ (201 Created)**:
```json
{
    "id": 1,
    "author": "username",
    "text": "Текст новой публикации",
    "pub_date": "2019-08-24T14:15:22Z",
    "image": null,
    "group": null
}
```

### Получение JWT токена

Отправьте POST-запрос на `/api/v1/jwt/create/` с вашими учетными данными:

```bash
curl -X POST -H "Content-Type: application/json" -d '{
    "username": "<ваш_логин>",
    "password": "<ваш_пароль>"
}' http://localhost:8000/api/v1/jwt/create/
```

**Ответ**:
```json
{
    "refresh": "<refresh_token>",
    "access": "<access_token>"
}
```
