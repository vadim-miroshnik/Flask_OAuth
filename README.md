# Проектная работа 7 спринта

https://github.com/dimkaddi/Auth_sprint_2

####


# Проектная работа 6 спринта

Ссылка на репозиторий

https://github.com/dimkaddi/Auth_sprint_1


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

Для ограничения запросов к эндойнтам сервисов необходимо использовать декоратор @rare_limit с параметром, который представляет собой ограничение количества запросов в секунду для каждого авторизованного пользователя

Добавлен дополнительный HTTP-заголовок X-Request-Id в NGINX для связки запросов. Проверка присутствия заголовка осуществляется в декораторе @app.before_request. 
