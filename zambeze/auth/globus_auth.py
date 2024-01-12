import os
import json
import time
import globus_sdk
from globus_sdk.scopes import TransferScopes


class GlobusAuthenticator:
    def __init__(self):
        self.client_id = os.getenv('GLOBUS_CLIENT_ID')
        if not self.client_id:
            raise ValueError("GLOBUS_CLIENT_ID is not set in environment variables.")
        self.auth_client = globus_sdk.NativeAppAuthClient(self.client_id)
        self.auth_client.oauth2_start_flow(refresh_tokens=True, requested_scopes=TransferScopes.all)
        self.tokens_dir = os.path.expanduser("~/.zambeze/tokens")

        if not os.path.exists(self.tokens_dir):
            os.makedirs(self.tokens_dir, mode=0o700)

    def authenticate(self):
        authorize_url = self.auth_client.oauth2_get_authorize_url()
        print(f"Please go to this URL and login:\n\n{authorize_url}\n")

        try:
            auth_code = input("Please enter the code here: ").strip()
            token_response = self.auth_client.oauth2_exchange_code_for_tokens(auth_code)

            self._save_tokens(token_response)
            return token_response
        except globus_sdk.GlobusError as e:
            print(f"An error occurred: {e}")
            return None

    def _save_tokens(self, token_response):
        transfer_data = token_response.by_resource_server['transfer.api.globus.org']
        tokens = {
            'access_token': transfer_data['access_token'],
            'refresh_token': transfer_data['refresh_token'],
            'expires_at': transfer_data['expires_at_seconds']
        }

        tokens_file = os.path.join(self.tokens_dir, 'globus_tokens.json')
        with open(tokens_file, 'w') as f:
            json.dump(tokens, f)

        # Make sure the tokens file is not accessible by others
        os.chmod(tokens_file, 0o600)

    def load_tokens(self):
        tokens_file = os.path.join(self.tokens_dir, 'globus_tokens.json')
        if not os.path.exists(tokens_file):
            return None

        with open(tokens_file, 'r') as f:
            return json.load(f)

    def refresh_access_token(self):
        tokens = self.load_tokens()
        if tokens and 'refresh_token' in tokens:
            try:
                response = self.auth_client.oauth2_refresh_token(tokens['refresh_token'])
                self._save_tokens(response)
                return response.by_resource_server['transfer.api.globus.org']['access_token']
            except globus_sdk.GlobusError as e:
                print(f"An error occurred while refreshing the token: {e}")
                return None
        return None

    def is_token_expired(self, expires_at):
        # Check if the current time is past the token's expiration time
        return time.time() > expires_at

    def check_tokens_and_authenticate(self, force_login=False):

        print("IN GLOBUS LOGIN FLOW! ")

        # Attempt to load the tokens
        tokens = self.load_tokens()

        if force_login:
            self.authenticate()

        if tokens:
            # Check if the access token has expired
            if self.is_token_expired(tokens['expires_at']):
                # Attempt to refresh the access token
                new_access_token = self.refresh_access_token()
                if new_access_token:
                    print("Access token has been successfully refreshed.")
                    return new_access_token
                else:
                    print("Failed to refresh access token, re-authenticating...")
            else:
                print("Loaded valid access token from file.")
                return tokens['access_token']

        # If there are no tokens or the tokens are expired and can't be refreshed, proceed with full authentication flow
        return self.authenticate()



