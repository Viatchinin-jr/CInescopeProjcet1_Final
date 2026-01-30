# # Я хз надо ли это поэтому закоментил

# import json
# from pydantic import ValidationError
#
# from const.roles import Roles
# import pytest
# from models.user_model import UserTest, CreateUserRequest
# from venv import logger
#
# def test_validate_test_user_fixtures(test_user):
#     user = UserTest.model_validate(test_user)
#     assert user.email
#
#
# def test_validate_creation_user_data(creation_user_data):
#     data = creation_user_data.model_validate(creation_user_data.model_dump())
#     assert data.banned is False
#     assert data.verified is not None
#
#
# def test_test_user_to_json_exclude_unset(test_user):
#     user = UserTest.model_validate(test_user)
#     json_data = user.model_dump_json(exclude_unset=True)
#     assert "banned" not in json_data
#     assert "verified" not in json_data
#
# def test_creation_user_data_to_json(creation_user_data):
#     user = creation_user_data.model_validate(creation_user_data)
#
#     json_str = user.model_dump_json() # без exclude_unset=tTrue
#     logger.info(f"creation_user_data json: {json_str}")
#
#     data = json.loads(json_str) # превращаем строку JSON в dict для проверок
#
#     assert data["banned"] is False
#     assert data["verified"] is True
#
#
# def test_validate_valid_user_dict():
#     """
#     Ментору - если я верно понял, можно и dict из фикстуры использовать.
#     Но тут видимо нужно именно ручками его передать.
#     """
#     valid_dict = {
#         "email": "whyssd@yandex.ru",
#         "fullName": "Nikta Viatchinin",
#         "password": "superpassword",
#         "passwordRepeat": "superpassword",
#         "roles": [Roles.USER.value],
#     }
#
#     user = UserTest.model_validate(valid_dict)
#     assert user.email == "whyssd@yandex.ru"
#     assert user.roles == [Roles.USER]
#
# def test_validate_invalid_user_dict():
#     invalid_dict = {
#         "email": "whyssdyandex.ru", # отсутствует "@"
#         "fullName": "Nikta Viatchinin",
#         "password": "superpassword",
#         "passwordRepeat": "superpassword",
#         "roles": [Roles.USER.value],
#     }
#
#     with pytest.raises(ValidationError):
#         UserTest.model_validate(invalid_dict)