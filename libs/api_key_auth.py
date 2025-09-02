import datetime
import json
import logging
import secrets

from mcp.server.auth.provider import OAuthAuthorizationServerProvider, AccessTokenT, AccessToken, RefreshTokenT, \
    AuthorizationCodeT, AuthorizationParams, AuthorizationCode, RefreshToken, construct_redirect_uri
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

from controllers.common.error import BadRequestError, UnauthorizedError
from service import ApiKeyService
from utils import jsonable_encoder

logger = logging.getLogger(__name__)


class ApiKeyAuthorizationServerProvider(OAuthAuthorizationServerProvider):

    async def load_access_token(self, token: str) -> AccessTokenT | None:
        logger.debug(f"Loading access token {token}")
        if ApiKeyService.validate_api_key(token):
            return AccessToken(token=token, expires_at=None, client_id="api_key", scopes=["user"])
        else:
            return None

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        logger.debug(f"Registering client {client_info}")
        data={"client_info",client_info.model_dump(exclude_none=True)}
        ApiKeyService.create_api_key(client_info.client_id,json.dumps(data),"mcp")

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        logger.debug(f"Getting client {client_id}")
        api_key = ApiKeyService.get_api_key_by_name(client_id)
        if not api_key:
            return None
        data=json.loads(api_key.description)
        return OAuthClientInformationFull.model_validate(data["client_info"])

    async def authorize(self, client: OAuthClientInformationFull, params: AuthorizationParams) -> str:
        logger.debug(f"Authorizing client {client} with params {params}")
        api_key = ApiKeyService.get_api_key_by_name(client.client_id)
        if not api_key:
            raise BadRequestError
        if client.client_id!=api_key.name:
            raise BadRequestError
        if client.scope and params.scopes:
            for scope in params.scopes:
                if scope not in client.scope.split(" "):
                    raise BadRequestError(f"Client was not registered with scope {scope}")
        if client.redirect_uris and params.redirect_uri:
            if params.redirect_uri not in client.redirect_uris:
                raise BadRequestError(f"Redirect URI '{params.redirect_uri}' not registered for client")
        params_dict = params.model_dump(exclude_none=True)
        params_dict["code"] = secrets.token_urlsafe(16)
        data={"client_info":client.model_dump(exclude_none=True),
              "auth_params":params_dict}
        ApiKeyService.update_api_key(api_key.id,api_key.name,json.dumps(jsonable_encoder(obj=data)),api_key.source)
        return construct_redirect_uri(str(params.redirect_uri), code=params_dict["code"], state=params.state)

    async def load_authorization_code(self, client: OAuthClientInformationFull,
                                      authorization_code: str) -> AuthorizationCodeT | None:
        logger.debug(f"Loading authorization code {authorization_code}")
        api_key = ApiKeyService.get_api_key_by_name(client.client_id)
        if not api_key:
            raise BadRequestError
        if client.client_id!=api_key.name:
            raise BadRequestError
        data=json.loads(api_key.description)
        params = data["auth_params"]
        auth_params=AuthorizationCode(
            code=params["code"],
            scopes=[client.scope],
            expires_at=datetime.datetime.now().timestamp()+30000,
            client_id=client.client_id,
            code_challenge=params["code_challenge"],
            redirect_uri=params["redirect_uri"],
            redirect_uri_provided_explicitly=params["redirect_uri_provided_explicitly"],
        )
        if auth_params.code != authorization_code:
            raise UnauthorizedError
        auth_params.client_id=client.client_id
        # 授权码失效时间30秒
        auth_params.expires_at=datetime.datetime.now().timestamp()+30000
        return auth_params

    async def exchange_authorization_code(self, client: OAuthClientInformationFull,
                                          authorization_code: AuthorizationCodeT) -> OAuthToken:
        logger.debug(f"Exchanging authorization code {authorization_code}")
        api_key = ApiKeyService.get_api_key_by_name(client.client_id)
        if not api_key:
            raise BadRequestError
        if client.client_id != api_key.name:
            raise BadRequestError
        if client.scope and authorization_code.scopes:
            for scope in authorization_code.scopes:
                if scope not in client.scope.split(" "):
                    raise BadRequestError(f"Client was not registered with scope {scope}")
        data = json.loads(api_key.description)
        auth_params = data["auth_params"]
        if auth_params['code'] != authorization_code.code:
            raise UnauthorizedError
        return OAuthToken(
            access_token=api_key.hash_key,
            expires_in=36000,
            refresh_token=api_key.api_key,
            scope=" ".join(authorization_code.scopes) if authorization_code.scopes else None,
        )

    async def load_refresh_token(self, client: OAuthClientInformationFull, refresh_token: str) -> RefreshTokenT | None:
        logger.debug(f"Loading refresh token {refresh_token}")
        api_key = ApiKeyService.get_api_key_by_name(client.client_id)
        if not api_key:
            raise BadRequestError
        if client.client_id != api_key.name:
            raise BadRequestError
        if api_key.api_key != refresh_token:
            raise UnauthorizedError
        return RefreshToken(token=refresh_token, client_id=client.client_id, scopes=[client.scope], expires_at=None)

    async def exchange_refresh_token(self, client: OAuthClientInformationFull, refresh_token: RefreshTokenT,
                                     scopes: list[str]) -> OAuthToken:
        logger.debug(f"Exchanging refresh token {refresh_token}")
        api_key = ApiKeyService.get_api_key_by_name(client.client_id)
        if not api_key:
            raise BadRequestError
        if client.client_id != api_key.name:
            raise BadRequestError
        if api_key.api_key != refresh_token.token:
            raise UnauthorizedError
        if client.scope and scopes:
            for scope in scopes:
                if scope not in client.scope.split(" "):
                    raise BadRequestError(f"Client was not registered with scope {scope}")
        return OAuthToken(
            access_token=api_key.hash_key,
            token_type="Bearer",
            expires_in=36000,
            refresh_token=api_key.api_key,
            scope=" ".join(scopes) if scopes else None,
        )

    async def revoke_token(self, token: AccessTokenT | RefreshTokenT) -> None:
        logger.debug(f"Revoking token {token}")
        # API Key模式不支持撤销token
        pass

