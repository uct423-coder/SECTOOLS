"""Tests for subnet calculator helpers."""

import ipaddress
from sectools.subnet_calc import _ip_class


def test_class_a():
    net = ipaddress.IPv4Network("10.0.0.0/8")
    assert _ip_class(net) == "A"


def test_class_b():
    net = ipaddress.IPv4Network("172.16.0.0/12")
    assert _ip_class(net) == "B"


def test_class_c():
    net = ipaddress.IPv4Network("192.168.1.0/24")
    assert _ip_class(net) == "C"


def test_class_d():
    net = ipaddress.IPv4Network("224.0.0.0/4")
    assert _ip_class(net) == "D (Multicast)"


def test_class_e():
    net = ipaddress.IPv4Network("240.0.0.0/4")
    assert _ip_class(net) == "E (Reserved)"
