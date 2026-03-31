BASE_URL = "https://auth.dev-cinescope.coconutqa.ru"
API_BASE_URL = "https://api.dev-cinescope.coconutqa.ru"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

#auth
LOGIN_ENDPOINT = "/login"
REGISTER_ENDPOINT = "/register"
LOGOUT_ENDPOINT = "/logout"
REFRESH_ENDPOINT = "/refresh-tokens"

#movies
MOVIES_ENDPOINT = "/movies"
MOVIES_ID_ENDPOINT = "/movies/{id}"


RED = "RED"
GREEN = "GREEN"
RESET = "RESET"