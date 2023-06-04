Flask
Flasgger
Marshmallow
SqlAlchemy
Flask Dance

## Работа с проектом

Запустить проект на продакшене:
    
    make prod_run

Сбилдить образ:

    make build 

Запустить окружение
  
    make run_environment

Запустить сервис или его тесты

    make run_service
    make run_tests

Swagger-схема доступна по:

http://127.0.0.1/apidocs

По дефолту создан пользователь superuser c паролем super_password

Для авторизации ендпоинтов в api в поле Authorization перед токеном необходимо добавлят JWT:

    JWT eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE2NzAyNTg0MDgsImlhdCI6MTY3MDI1NzgwOCwibmJmIjoxNjcwMjU3ODA4LCJzdWIiOiJcImI5NjZhOGVjMmZiNTRlYjFiNmRiMTYwZDMwZDQ1YzdkXCIiLCJyb2xlIjoic3VwZXJ1c2VyIn0.zwysTVm9vkkGYIVB76GyDfW47TlioP0tYuTxOyciSs0

### Ограничитель запросов
Для ограничения запросов к эндойнтам сервисов необходимо использовать декоратор @rare_limit с параметром, который представляет собой ограничение количества запросов в секунду для каждого авторизованного пользователя
Для задержки выполнения запросов предусмотрен параметр delay в
        
    def ratelimit(
            self,
            *identities: str,
            delay: bool = False,
            max_delay: Union[int, float] = None,
        ),
   
который используется при реализации декоратора в методе

    def delay_or_reraise(self, err: BucketFullException) -> float`

Если delay = False, то ответы будут сразу выдаваться с ошибкой 429:

        if self.delay and not exceeded_max_delay:
            return delay_time
        abort(429, description="Too many requests")

### HTTP-заголовок для трассировки
Добавлен дополнительный HTTP-заголовок X-Request-Id в NGINX для связки запросов. Проверка присутствия заголовка осуществляется в декораторе @app.before_request. 
