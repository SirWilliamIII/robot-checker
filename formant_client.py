import logging
import requests

NUM_RETRIES = 5

class FormantClientRequestError(Exception):
    message: str
    retryable: bool

    def __init__(self, message: str, retryable: bool = True):
        self.message = message
        self.retryable = retryable

    def __str__(self):
        return f"FormantClientRequestError: {self.message}"


def formant_client_retry_on_failure(max_retries, propegrate_error=True):
    """
    Retry a function call on a GaussianClientRequestError up to max_retries times
    @param `max_retries`: The maximum number of times to retry the function call
    @param `propegrate_error`: If True, raise a GaussianClientRequestError if the function call fails after max_retries attempts. If False, return None
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except FormantClientRequestError as e:                    
                    if not e.retryable:
                        raise e
                    logging.warning(
                        f"Request failed with error: {e}. Retrying ({i + 1}/{max_retries})"
                    )

            # If we get here, we've exceeded the number of retries
            if propegrate_error:
                raise FormantClientRequestError(
                    f"Request failed after {max_retries} retries"
                )
            return None

        return wrapper

    return decorator

class FormantClient:
    def __init__(
        self,
        admin_api_endpoint,
        formant_email,
        formant_password,
    ):
        self._admin_api_endpoint = admin_api_endpoint
        self._email = formant_email
        self._password = formant_password

        self._authenticated_headers = {}

    def _get_get_admin_endpoint(self, path: str) -> str:
        """
        Returns the admin endpoint for the given path.
        @param `path`: The path to the endpoint. (e.g. /auth/login)
        """
        return f"{self._admin_api_endpoint}{path}"

    @formant_client_retry_on_failure(max_retries=NUM_RETRIES)
    def _authenticate(self):
        """
        Authenticate with Formant and store the auth headers.
        """
        if len(self._authenticated_headers) > 0:
            return

        body = {
            "email": self._email,
            "password": self._password,
            "tokenExpirationSeconds": 86400,
        }

        response = requests.post(
            url=self._get_get_admin_endpoint("/auth/login"), json=body
        )

        if response.status_code == 200:
            response_json = response.json()

            self._authenticated_headers = {
                "authorization": f"Bearer {response_json['authentication']['accessToken']}",
                "content-type": "application/json",
            }
        else:
            raise FormantClientRequestError(
                f"Failed to authenticate... {response.text}"
            )

    def _get_authenticated_headers(self):
        """
        Return the headers for an authenticated request.
        """
        self._authenticate()
        return self._authenticated_headers

    @formant_client_retry_on_failure(max_retries=NUM_RETRIES)
    def query_robots(self, tags: dict = {}, enabled_only: bool = False):
        """
        Query robots with the given tags.
        @param `tags`: The tags to query for (form of {tag_key: [tag_value]})
        """
        body = {"tags": tags}

        if enabled_only:
            body["enabled"] = True

        response = requests.post(
            url=self._get_get_admin_endpoint("/devices/query"),
            headers=self._get_authenticated_headers(),
            json=body,
        )

        if response.status_code == 200:
            try:
                return response.json()["items"]
            except Exception as e:
                raise FormantClientRequestError(f"Failed to query robots: {e}")
        else:
            raise FormantClientRequestError(
                f"Failed to query robots... {response.text}"
            )

    @formant_client_retry_on_failure(max_retries=NUM_RETRIES)
    def get_task_list_for_device_sync(
        self,
        deviceId: str,
    ):
        """
        Get all task summaries for a given device in a given time range.
        @param `deviceId` - Robot Identification Number (Gaussian Serial Number)
        """

        task_summaries = []

        page_offset = 0
        page_size = 100

        endpoint = self._get_get_admin_endpoint("/events/query")

        while 1:
            params = {
                    "eventTypes": ["task-summary"],
                    "count": page_size,
                    "offset": page_offset,
                    "deviceIds": [deviceId]
                }
            
            response = requests.post(
                url=endpoint, headers=self._get_authenticated_headers(), json=params
            )

            if response.status_code != 200:
                    raise FormantClientRequestError(
                        f"Failed to get task summaries... code: {response.status}. error: {response.text}"
                    )
            
            task_summaries.extend(response.json()["items"])

            if len(response.json()["items"]) < page_size:
                break

            page_offset += page_size
        
        return task_summaries

