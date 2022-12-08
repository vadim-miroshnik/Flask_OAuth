# Проектная работа 7 спринта

Упростите регистрацию и аутентификацию пользователей в Auth-сервисе, добавив вход через социальные сервисы. Список сервисов выбирайте исходя из целевой аудитории онлайн-кинотеатра — подумайте, какими социальными сервисами они пользуются. Например, использовать [OAuth от Github](https://docs.github.com/en/free-pro-team@latest/developers/apps/authorizing-oauth-apps){target="_blank"} — не самая удачная идея. Ваши пользователи не разработчики и вряд ли имеют аккаунт на Github. А вот добавить Twitter, Facebook, VK, Google, Yandex или Mail будет хорошей идеей.

Вам не нужно делать фронтенд в этой задаче и реализовывать собственный сервер OAuth. Нужно реализовать протокол со стороны потребителя.

Информация по OAuth у разных поставщиков данных: 

- [Twitter](https://developer.twitter.com/en/docs/authentication/overview){target="_blank"},
- [Facebook](https://developers.facebook.com/docs/facebook-login/){target="_blank"},
- [VK](https://vk.com/dev/access_token){target="_blank"},
- [Google](https://developers.google.com/identity/protocols/oauth2){target="_blank"},
- [Yandex](https://yandex.ru/dev/oauth/?turbo=true){target="_blank"},
- [Mail](https://api.mail.ru/docs/guides/oauth/){target="_blank"}.

## Дополнительное задание

Реализуйте возможность открепить аккаунт в соцсети от личного кабинета. 

Решение залейте в репозиторий текущего спринта и отправьте на ревью.


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