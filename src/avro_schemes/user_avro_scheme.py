user = {
    "namespace": "user",
    "name": "UserData",
    "type": "record",
    "doc": "Информация о пользователе",
    "fields": [
        {"name": "pk", "type": "string", "doc": "Идентификатор", "logicalType": "uuid"},
        {"name": "name", "type": "string", "doc": "Имя"},
        {"name": "email", "type": "string", "doc": "Электронная почта"},
    ],
}
