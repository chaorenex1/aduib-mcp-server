# from contextvars import ContextVar
#
# from libs.contextVar_wrapper import ContextVarWrappers
# from models.api_key import ApiKey
#
# api_key_context: ContextVarWrappers[ApiKey]=ContextVarWrappers(ContextVar("api_key"))
# trace_id_context: ContextVarWrappers[str]=ContextVarWrappers(ContextVar("trace_id"))
from contextvars import ContextVar

from aduib_app import AduibAIApp
from fast_mcp import FastMCP
from libs.contextVar_wrapper import ContextVarWrappers

app_context: ContextVarWrappers[AduibAIApp]=ContextVarWrappers(ContextVar("app_context"))
mcp_context: ContextVarWrappers[FastMCP]=ContextVarWrappers(ContextVar("mcp_context"))