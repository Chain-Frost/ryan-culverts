"""Prismatic open-channel geometry and uniform-flow calculations."""

from .geometry import OpenChannelSection, RectangularChannel, TrapezoidalChannel
from .uniform import ChannelNormalDepthResult, calculate_channel_normal_depth

__all__: list[str] = [
    "ChannelNormalDepthResult",
    "OpenChannelSection",
    "RectangularChannel",
    "TrapezoidalChannel",
    "calculate_channel_normal_depth",
]
