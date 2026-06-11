"""OpenClaw control service facade — composed from focused mixins.

Each capability (status, install, config, gateway, channels, agents) lives in its
own module; this class just wires them together. Adding a feature means editing
one small mixin, not a 800-line file.
"""
from __future__ import annotations

from ._agents import AgentsMixin
from ._bindings import BindingsMixin
from ._channels import ChannelsMixin
from ._documents import AgentDocumentsMixin
from ._support import SupportMixin
from ._config_ops import ConfigMixin
from ._gateway import GatewayMixin
from ._install_ops import InstallMixin
from ._status import StatusMixin


class OpenClawService(
    StatusMixin,
    InstallMixin,
    ConfigMixin,
    GatewayMixin,
    ChannelsMixin,
    AgentsMixin,
    BindingsMixin,
    AgentDocumentsMixin,
    SupportMixin,
):
    """Friendly front-end for OpenClaw: detect, install, configure, operate."""
