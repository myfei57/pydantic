import json
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from typing import Annotated, Any

import pytest

from pydantic import (
    BaseModel,
    IPvAnyAddress,
    IPvAnyInterface,
    IPvAnyNetwork,
    PydanticUserError,
    TypeAdapter,
    ValidationError,
)
from pydantic.config import ConfigDict
from pydantic.networks import NetworkConstraints


@pytest.mark.parametrize(
    'value,cls',
    [
        ('0.0.0.0', IPv4Address),
        ('1.1.1.1', IPv4Address),
        ('10.10.10.10', IPv4Address),
        ('192.168.0.1', IPv4Address),
        ('255.255.255.255', IPv4Address),
        ('::1:0:1', IPv6Address),
        ('ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff', IPv6Address),
        (b'\x00\x00\x00\x00', IPv4Address),
        (b'\x01\x01\x01\x01', IPv4Address),
        (b'\n\n\n\n', IPv4Address),
        (b'\xc0\xa8\x00\x01', IPv4Address),
        (b'\xff\xff\xff\xff', IPv4Address),
        (b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x01', IPv6Address),
        (b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff', IPv6Address),
        (0, IPv4Address),
        (16_843_009, IPv4Address),
        (168_430_090, IPv4Address),
        (3_232_235_521, IPv4Address),
        (4_294_967_295, IPv4Address),
        (4_294_967_297, IPv6Address),
        (340_282_366_920_938_463_463_374_607_431_768_211_455, IPv6Address),
        (IPv4Address('192.168.0.1'), IPv4Address),
        (IPv6Address('::1:0:1'), IPv6Address),
    ],
)
def test_ipaddress_success(value, cls):
    class Model(BaseModel):
        ip: IPvAnyAddress

    assert Model(ip=value).ip == cls(value)


@pytest.mark.parametrize(
    'value',
    [
        '0.0.0.0',
        '1.1.1.1',
        '10.10.10.10',
        '192.168.0.1',
        '255.255.255.255',
        b'\x00\x00\x00\x00',
        b'\x01\x01\x01\x01',
        b'\n\n\n\n',
        b'\xc0\xa8\x00\x01',
        b'\xff\xff\xff\xff',
        0,
        16_843_009,
        168_430_090,
        3_232_235_521,
        4_294_967_295,
        IPv4Address('0.0.0.0'),
        IPv4Address('1.1.1.1'),
        IPv4Address('10.10.10.10'),
        IPv4Address('192.168.0.1'),
        IPv4Address('255.255.255.255'),
    ],
)
def test_ipv4address_success(value):
    class Model(BaseModel):
        ipv4: IPv4Address

    assert Model(ipv4=value).ipv4 == IPv4Address(value)


@pytest.mark.parametrize(
    'tp,value,errors',
    [
        (
            IPv4Address,
            IPv4Address('0.0.0.0'),
            [
                {
                    'type': 'is_instance_of',
                    'loc': ('v',),
                    'msg': 'Input should be an instance of IPv4Address',
                    'input': '0.0.0.0',
                    'ctx': {'class': 'IPv4Address'},
                }
            ],
        ),
        (
            IPv4Interface,
            IPv4Interface('192.168.0.0/24'),
            [
                {
                    'type': 'is_instance_of',
                    'loc': ('v',),
                    'msg': 'Input should be an instance of IPv4Interface',
                    'input': '192.168.0.0/24',
                    'ctx': {'class': 'IPv4Interface'},
                }
            ],
        ),
        (
            IPv4Network,
            IPv4Network('192.168.0.0/24'),
            [
                {
                    'type': 'is_instance_of',
                    'loc': ('v',),
                    'msg': 'Input should be an instance of IPv4Network',
                    'input': '192.168.0.0/24',
                    'ctx': {'class': 'IPv4Network'},
                }
            ],
        ),
        (
            IPv6Address,
            IPv6Address('::1:0:1'),
            [
                {
                    'type': 'is_instance_of',
                    'loc': ('v',),
                    'msg': 'Input should be an instance of IPv6Address',
                    'input': '::1:0:1',
                    'ctx': {'class': 'IPv6Address'},
                }
            ],
        ),
        (
            IPv6Interface,
            IPv6Interface('2001:db00::0/120'),
            [
                {
                    'type': 'is_instance_of',
                    'loc': ('v',),
                    'msg': 'Input should be an instance of IPv6Interface',
                    'input': '2001:db00::/120',
                    'ctx': {'class': 'IPv6Interface'},
                }
            ],
        ),
        (
            IPv6Network,
            IPv6Network('2001:db00::0/120'),
            [
                {
                    'type': 'is_instance_of',
                    'loc': ('v',),
                    'msg': 'Input should be an instance of IPv6Network',
                    'input': '2001:db00::/120',
                    'ctx': {'class': 'IPv6Network'},
                }
            ],
        ),
    ],
)
def test_ip_strict(tp: Any, value: Any, errors: list[Any]) -> None:
    class Model(BaseModel):
        v: tp

        model_config = ConfigDict(strict=True)

    with pytest.raises(ValidationError) as exc_info:
        Model(v=str(value))
    assert exc_info.value.errors(include_url=False) == errors

    assert Model(v=value).v == value


@pytest.mark.parametrize(
    'value',
    [
        '::1:0:1',
        'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff',
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x01',
        b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff',
        4_294_967_297,
        340_282_366_920_938_463_463_374_607_431_768_211_455,
        IPv6Address('::1:0:1'),
        IPv6Address('ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff'),
    ],
)
def test_ipv6address_success(value):
    class Model(BaseModel):
        ipv6: IPv6Address

    assert Model(ipv6=value).ipv6 == IPv6Address(value)


@pytest.mark.parametrize('value', ['hello,world', '192.168.0.1.1.1', -1, 2**128 + 1])
def test_ipaddress_fails(value):
    class Model(BaseModel):
        ip: IPvAnyAddress

    with pytest.raises(ValidationError) as exc_info:
        Model(ip=value)
    assert exc_info.value.error_count() == 1
    assert exc_info.value.errors(include_url=False)[0] == {
        'type': 'ip_any_address',
        'loc': ('ip',),
        'msg': 'value is not a valid IPv4 or IPv6 address',
        'input': value,
    }


@pytest.mark.parametrize('value', ['hello,world', '192.168.0.1.1.1', -1, 2**32 + 1, IPv6Address('::0:1:0')])
def test_ipv4address_fails(value):
    class Model(BaseModel):
        ipv4: IPv4Address

    with pytest.raises(ValidationError) as exc_info:
        Model(ipv4=value)
    assert exc_info.value.error_count() == 1
    assert exc_info.value.errors(include_url=False)[0] == {
        'type': 'ip_v4_address',
        'loc': ('ipv4',),
        'msg': 'Input is not a valid IPv4 address',
        'input': value,
    }


@pytest.mark.parametrize('value', ['hello,world', '192.168.0.1.1.1', -1, 2**128 + 1, IPv4Address('192.168.0.1')])
def test_ipv6address_fails(value):
    class Model(BaseModel):
        ipv6: IPv6Address

    with pytest.raises(ValidationError) as exc_info:
        Model(ipv6=value)
    assert exc_info.value.error_count() == 1
    # insert_assert(exc_info.value.errors(include_url=False)[0])
    assert exc_info.value.errors(include_url=False)[0] == {
        'type': 'ip_v6_address',
        'loc': ('ipv6',),
        'msg': 'Input is not a valid IPv6 address',
        'input': value,
    }


@pytest.mark.parametrize(
    'value,cls',
    [
        ('192.168.0.0/24', IPv4Network),
        ('192.168.128.0/30', IPv4Network),
        ('2001:db00::0/120', IPv6Network),
        (2**32 - 1, IPv4Network),  # no mask equals to mask /32
        (20_282_409_603_651_670_423_947_251_286_015, IPv6Network),  # /128
        (b'\xff\xff\xff\xff', IPv4Network),  # /32
        (b'\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff', IPv6Network),
        (('192.168.0.0', 24), IPv4Network),
        (('2001:db00::0', 120), IPv6Network),
        (IPv4Network('192.168.0.0/24'), IPv4Network),
    ],
)
def test_ipnetwork_success(value, cls):
    class Model(BaseModel):
        ip: IPvAnyNetwork = None

    assert Model(ip=value).ip == cls(value)


@pytest.mark.parametrize(
    'value,cls',
    [
        ('192.168.0.0/24', IPv4Network),
        ('192.168.128.0/30', IPv4Network),
        (2**32 - 1, IPv4Network),  # no mask equals to mask /32
        (b'\xff\xff\xff\xff', IPv4Network),  # /32
        (('192.168.0.0', 24), IPv4Network),
        (IPv4Network('192.168.0.0/24'), IPv4Network),
    ],
)
def test_ip_v4_network_success(value, cls):
    class Model(BaseModel):
        ip: IPv4Network = None

    assert Model(ip=value).ip == cls(value)


@pytest.mark.parametrize(
    'value,cls',
    [
        ('2001:db00::0/120', IPv6Network),
        (20_282_409_603_651_670_423_947_251_286_015, IPv6Network),  # /128
        (b'\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff', IPv6Network),
        (('2001:db00::0', 120), IPv6Network),
        (IPv6Network('2001:db00::0/120'), IPv6Network),
    ],
)
def test_ip_v6_network_success(value, cls):
    class Model(BaseModel):
        ip: IPv6Network = None

    assert Model(ip=value).ip == cls(value)


@pytest.mark.parametrize('value', ['hello,world', '192.168.0.1.1.1/24', -1, 2**128 + 1])
def test_ipnetwork_fails(value):
    class Model(BaseModel):
        ip: IPvAnyNetwork = None

    with pytest.raises(ValidationError) as exc_info:
        Model(ip=value)
    assert exc_info.value.error_count() == 1
    # insert_assert(exc_info.value.errors(include_url=False)[0])
    assert exc_info.value.errors(include_url=False)[0] == {
        'type': 'ip_any_network',
        'loc': ('ip',),
        'msg': 'value is not a valid IPv4 or IPv6 network',
        'input': value,
    }


@pytest.mark.parametrize('value', ['hello,world', '192.168.0.1.1.1/24', -1, 2**128 + 1, '2001:db00::1/120'])
def test_ip_v4_network_fails(value):
    class Model(BaseModel):
        ip: IPv4Network = None

    with pytest.raises(ValidationError) as exc_info:
        Model(ip=value)
    assert exc_info.value.error_count() == 1
    # insert_assert(exc_info.value.errors(include_url=False)[0])
    assert exc_info.value.errors(include_url=False)[0] == {
        'type': 'ip_v4_network',
        'loc': ('ip',),
        'msg': 'Input is not a valid IPv4 network',
        'input': value,
    }


@pytest.mark.parametrize('value', ['hello,world', '192.168.0.1.1.1/24', -1, 2**128 + 1, '192.168.0.1/24'])
def test_ip_v6_network_fails(value):
    class Model(BaseModel):
        ip: IPv6Network = None

    with pytest.raises(ValidationError) as exc_info:
        Model(ip=value)

    assert exc_info.value.error_count() == 1
    # insert_assert(exc_info.value.errors(include_url=False)[0])
    assert exc_info.value.errors(include_url=False)[0] == {
        'type': 'ip_v6_network',
        'loc': ('ip',),
        'msg': 'Input is not a valid IPv6 network',
        'input': value,
    }


def test_ipvany_serialization():
    class Model(BaseModel):
        address: IPvAnyAddress
        network: IPvAnyNetwork
        interface: IPvAnyInterface

    m = Model(address='127.0.0.1', network='192.0.2.0/27', interface='127.0.0.1/32')
    assert json.loads(m.model_dump_json()) == {
        'address': '127.0.0.1',
        'interface': '127.0.0.1/32',
        'network': '192.0.2.0/27',
    }


@pytest.mark.parametrize(
    'value,cls',
    [
        ('192.168.0.0/24', IPv4Interface),
        ('192.168.0.1/24', IPv4Interface),
        ('192.168.128.0/30', IPv4Interface),
        ('192.168.128.1/30', IPv4Interface),
        ('2001:db00::0/120', IPv6Interface),
        ('2001:db00::1/120', IPv6Interface),
        (2**32 - 1, IPv4Interface),  # no mask equals to mask /32
        (20_282_409_603_651_670_423_947_251_286_015, IPv6Interface),  # /128
        (20_282_409_603_651_670_423_947_251_286_014, IPv6Interface),
        (b'\xff\xff\xff\xff', IPv4Interface),  # /32
        (b'\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff', IPv6Interface),
        (('192.168.0.0', 24), IPv4Interface),
        (('192.168.0.1', 24), IPv4Interface),
        (('2001:db00::0', 120), IPv6Interface),
        (('2001:db00::1', 120), IPv6Interface),
        (IPv4Interface('192.168.0.0/24'), IPv4Interface),
        (IPv4Interface('192.168.0.1/24'), IPv4Interface),
        (IPv6Interface('2001:db00::0/120'), IPv6Interface),
        (IPv6Interface('2001:db00::1/120'), IPv6Interface),
    ],
)
def test_ipinterface_success(value, cls):
    class Model(BaseModel):
        ip: IPvAnyInterface

    assert Model(ip=value).ip == cls(value)


@pytest.mark.parametrize(
    'value,cls',
    [
        ('192.168.0.0/24', IPv4Interface),
        ('192.168.0.1/24', IPv4Interface),
        ('192.168.128.0/30', IPv4Interface),
        ('192.168.128.1/30', IPv4Interface),
        (2**32 - 1, IPv4Interface),  # no mask equals to mask /32
        (b'\xff\xff\xff\xff', IPv4Interface),  # /32
        (('192.168.0.0', 24), IPv4Interface),
        (('192.168.0.1', 24), IPv4Interface),
        (IPv4Interface('192.168.0.0/24'), IPv4Interface),
        (IPv4Interface('192.168.0.1/24'), IPv4Interface),
    ],
)
def test_ip_v4_interface_success(value, cls):
    class Model(BaseModel):
        ip: IPv4Interface

    assert Model(ip=value).ip == cls(value)


@pytest.mark.parametrize(
    'value,cls',
    [
        ('2001:db00::0/120', IPv6Interface),
        ('2001:db00::1/120', IPv6Interface),
        (20_282_409_603_651_670_423_947_251_286_015, IPv6Interface),  # /128
        (20_282_409_603_651_670_423_947_251_286_014, IPv6Interface),
        (b'\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff', IPv6Interface),
        (('2001:db00::0', 120), IPv6Interface),
        (('2001:db00::1', 120), IPv6Interface),
        (IPv6Interface('2001:db00::0/120'), IPv6Interface),
        (IPv6Interface('2001:db00::1/120'), IPv6Interface),
    ],
)
def test_ip_v6_interface_success(value, cls):
    class Model(BaseModel):
        ip: IPv6Interface = None

    assert Model(ip=value).ip == cls(value)


@pytest.mark.parametrize('value', ['hello,world', '192.168.0.1.1.1/24', -1, 2**128 + 1])
def test_ipinterface_fails(value):
    class Model(BaseModel):
        ip: IPvAnyInterface = None

    with pytest.raises(ValidationError) as exc_info:
        Model(ip=value)

    assert exc_info.value.error_count() == 1
    # insert_assert(exc_info.value.errors(include_url=False)[0])
    assert exc_info.value.errors(include_url=False)[0] == {
        'type': 'ip_any_interface',
        'loc': ('ip',),
        'msg': 'value is not a valid IPv4 or IPv6 interface',
        'input': value,
    }


@pytest.mark.parametrize('value', ['hello,world', '192.168.0.1.1.1/24', -1, 2**128 + 1])
def test_ip_v4_interface_fails(value):
    class Model(BaseModel):
        ip: IPv4Interface = None

    with pytest.raises(ValidationError) as exc_info:
        Model(ip=value)

    assert exc_info.value.error_count() == 1
    # insert_assert(exc_info.value.errors(include_url=False)[0])
    assert exc_info.value.errors(include_url=False)[0] == {
        'type': 'ip_v4_interface',
        'loc': ('ip',),
        'msg': 'Input is not a valid IPv4 interface',
        'input': value,
    }


@pytest.mark.parametrize('value', ['hello,world', '192.168.0.1.1.1/24', -1, 2**128 + 1])
def test_ip_v6_interface_fails(value):
    class Model(BaseModel):
        ip: IPv6Interface = None

    with pytest.raises(ValidationError) as exc_info:
        Model(ip=value)

    assert exc_info.value.error_count() == 1
    # insert_assert(exc_info.value.errors(include_url=False)[0])
    assert exc_info.value.errors(include_url=False)[0] == {
        'type': 'ip_v6_interface',
        'loc': ('ip',),
        'msg': 'Input is not a valid IPv6 interface',
        'input': value,
    }


@pytest.mark.parametrize(
    'ip_type,allowed_networks,value',
    [
        (IPv4Address, ['10.0.0.0/8', '192.168.0.0/16'], '10.0.0.1'),
        (IPv4Address, ['192.168.0.0/24'], '192.168.0.123'),
        (IPv6Address, ['2001:db8::/32'], '2001:db8::1'),
        (IPv6Address, ['::1/128'], '::1'),
        (IPvAnyAddress, ['10.0.0.0/8', '2001:db8::/32'], '10.0.0.1'),
        (IPvAnyAddress, ['10.0.0.0/8', '2001:db8::/32'], '2001:db8::1'),
        # no allowed list means the allowed range is unrestricted:
        (IPv4Address, None, '8.8.8.8'),
        (IPvAnyAddress, None, '8.8.8.8'),
        (IPvAnyAddress, None, '2001:db9::1'),
    ],
)
def test_network_constraints_allowed(ip_type, allowed_networks, value):
    ta = TypeAdapter(Annotated[ip_type, NetworkConstraints(allowed_networks=allowed_networks)])
    assert ta.validate_python(value) == ip_type(value)


def test_network_constraints_returns_original_address_object() -> None:
    ta = TypeAdapter(Annotated[IPv4Address, NetworkConstraints(allowed_networks=['10.0.0.0/8'])])
    result = ta.validate_python(IPv4Address('10.0.0.1'))
    assert type(result) is IPv4Address
    assert result == IPv4Address('10.0.0.1')

    ta_any = TypeAdapter(Annotated[IPvAnyAddress, NetworkConstraints(denied_networks=['10.0.0.0/8'])])
    assert type(ta_any.validate_python('2001:db8::1')) is IPv6Address


@pytest.mark.parametrize(
    'ip_type,allowed_networks,value',
    [
        (IPv4Address, ['10.0.0.0/8'], '192.168.0.1'),
        (IPv6Address, ['2001:db8::/32'], '2001:db9::1'),
        (IPvAnyAddress, ['10.0.0.0/8', '2001:db8::/32'], '8.8.8.8'),
        (IPvAnyAddress, ['10.0.0.0/8', '2001:db8::/32'], '2001:db9::1'),
    ],
)
def test_network_constraints_not_allowed(ip_type, allowed_networks, value):
    ta = TypeAdapter(Annotated[ip_type, NetworkConstraints(allowed_networks=allowed_networks)])
    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(value)
    assert exc_info.value.errors(include_url=False)[0] == {
        'type': 'ip_address_not_allowed',
        'loc': (),
        'msg': f'IP address {value} is not a member of any allowed network',
        'input': value,
        'ctx': {'ip': value},
    }


def test_network_constraints_denied_takes_precedence() -> None:
    ta = TypeAdapter(
        Annotated[
            IPv4Address,
            NetworkConstraints(allowed_networks=['10.0.0.0/8'], denied_networks=['10.1.0.0/16']),
        ]
    )
    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python('10.1.0.1')
    assert exc_info.value.errors(include_url=False)[0] == {
        'type': 'ip_address_denied',
        'loc': (),
        'msg': 'IP address 10.1.0.1 belongs to the denied network 10.1.0.0/16',
        'input': '10.1.0.1',
        'ctx': {'ip': '10.1.0.1', 'network': '10.1.0.0/16'},
    }

    # addresses outside the denied network but inside an allowed network still pass
    assert ta.validate_python('10.2.0.1') == IPv4Address('10.2.0.1')

    # denied also rejects when no allowed list is configured
    deny_only = TypeAdapter(Annotated[IPvAnyAddress, NetworkConstraints(denied_networks=['10.0.0.0/8'])])
    assert deny_only.validate_python('8.8.8.8') == IPv4Address('8.8.8.8')
    with pytest.raises(ValidationError) as exc_info:
        deny_only.validate_python('10.255.255.255')
    assert exc_info.value.errors(include_url=False)[0]['type'] == 'ip_address_denied'


@pytest.mark.parametrize('value', ['10.0.0.1', '8.8.8.8', '0.0.0.0'])
def test_network_constraints_empty_allowed_denies_everything(value) -> None:
    ta = TypeAdapter(Annotated[IPv4Address, NetworkConstraints(allowed_networks=[])])
    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(value)
    assert exc_info.value.errors(include_url=False)[0]['type'] == 'ip_address_not_allowed'

    # networks of the other family cannot match either
    ta_v4_with_v6_networks = TypeAdapter(Annotated[IPv4Address, NetworkConstraints(allowed_networks=['2001:db8::/32'])])
    with pytest.raises(ValidationError) as exc_info:
        ta_v4_with_v6_networks.validate_python('10.0.0.1')
    assert exc_info.value.errors(include_url=False)[0]['type'] == 'ip_address_not_allowed'


@pytest.mark.parametrize(
    'network,value',
    [
        ('192.168.0.0/24', '192.168.0.0'),  # network address
        ('192.168.0.0/24', '192.168.0.255'),  # broadcast address
        ('10.0.0.0/8', '10.255.255.255'),
        ('2001:db8::/120', '2001:db8::0'),
        ('2001:db8::/120', '2001:db8::ff'),
    ],
)
def test_network_constraints_includes_network_endpoints(network, value) -> None:
    ip_type = IPv6Address if ':' in value else IPv4Address
    ta = TypeAdapter(Annotated[ip_type, NetworkConstraints(allowed_networks=[network])])
    assert ta.validate_python(value) == ip_type(value)


def test_network_constraints_match_families_separately() -> None:
    ta = TypeAdapter(
        Annotated[
            IPvAnyAddress,
            NetworkConstraints(
                allowed_networks=['10.0.0.0/8', '2001:db8::/32'],
                denied_networks=['10.1.0.0/16', '2001:db8:1::/48'],
            ),
        ]
    )
    assert ta.validate_python('10.0.0.1') == IPv4Address('10.0.0.1')
    assert ta.validate_python('2001:db8:2::1') == IPv6Address('2001:db8:2::1')

    for value, error_type in [
        ('10.1.0.1', 'ip_address_denied'),
        ('2001:db8:1::1', 'ip_address_denied'),
        ('192.168.0.1', 'ip_address_not_allowed'),
        ('2001:db9::1', 'ip_address_not_allowed'),
    ]:
        with pytest.raises(ValidationError) as exc_info:
            ta.validate_python(value)
        assert exc_info.value.errors(include_url=False)[0]['type'] == error_type


def test_network_constraints_field_location_preserved() -> None:
    class Model(BaseModel):
        ip: Annotated[IPv4Address, NetworkConstraints(allowed_networks=['10.0.0.0/8'])]

    with pytest.raises(ValidationError) as exc_info:
        Model(ip='8.8.8.8')
    error = exc_info.value.errors(include_url=False)[0]
    assert error['loc'] == ('ip',)
    assert error['type'] == 'ip_address_not_allowed'


def test_network_constraints_containers(container_class) -> None:
    class Container(container_class):
        ip: Annotated[IPv4Address, NetworkConstraints(allowed_networks=['10.0.0.0/8'])]

    ta = TypeAdapter(Container)
    assert ta.dump_python(ta.validate_python({'ip': '10.0.0.1'})) == {'ip': IPv4Address('10.0.0.1')}

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python({'ip': '8.8.8.8'})
    error = exc_info.value.errors(include_url=False)[0]
    assert error['loc'] == ('ip',)
    assert error['type'] == 'ip_address_not_allowed'


def test_network_constraints_parse_error_preserved() -> None:
    # an address that cannot be parsed reports the regular address error, not a network error
    ta = TypeAdapter(Annotated[IPv4Address, NetworkConstraints(allowed_networks=['10.0.0.0/8'])])
    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python('not-an-ip')
    assert exc_info.value.errors(include_url=False)[0]['type'] == 'ip_v4_address'


def test_network_constraints_strict_mode() -> None:
    class Model(BaseModel):
        model_config = ConfigDict(strict=True)
        ip: Annotated[IPv4Address, NetworkConstraints(allowed_networks=['10.0.0.0/8'])]

    assert Model(ip=IPv4Address('10.0.0.1')).ip == IPv4Address('10.0.0.1')
    with pytest.raises(ValidationError) as exc_info:
        Model(ip=IPv4Address('8.8.8.8'))
    assert exc_info.value.errors(include_url=False)[0]['type'] == 'ip_address_not_allowed'


@pytest.mark.parametrize(
    'field_name,bad_network,message_part',
    [
        ('allowed_networks', '192.168.0.1/24', 'has host bits set'),
        ('allowed_networks', '2001:db8::1/64', 'has host bits set'),
        ('allowed_networks', 'not-a-network', 'does not appear to be an IPv4 or IPv6 network'),
        ('allowed_networks', '1.2.3.4/99', 'not a valid canonical CIDR network'),
        ('denied_networks', '10.0.0.1/8', 'has host bits set'),
    ],
)
def test_network_constraints_invalid_networks_raise_at_build_time(field_name, bad_network, message_part) -> None:
    # the error is raised while building the TypeAdapter, before any value is validated
    with pytest.raises(PydanticUserError, match=message_part):
        TypeAdapter(Annotated[IPv4Address, NetworkConstraints(**{field_name: [bad_network]})])

    # ... and while defining the model class, instead of waiting for data to hit the constraint
    with pytest.raises(PydanticUserError, match=message_part):

        class BadModel(BaseModel):
            ip: Annotated[IPv4Address, NetworkConstraints(**{field_name: [bad_network]})]


def test_network_constraints_invalid_network_item_type() -> None:
    with pytest.raises(PydanticUserError, match='CIDR strings or `ipaddress` network objects'):
        TypeAdapter(Annotated[IPv4Address, NetworkConstraints(allowed_networks=[10])])


@pytest.mark.parametrize('unsupported_type', [str, int, IPv4Network, IPvAnyNetwork])
def test_network_constraints_rejects_unsupported_types(unsupported_type) -> None:
    with pytest.raises(PydanticUserError) as exc_info:
        TypeAdapter(Annotated[unsupported_type, NetworkConstraints(allowed_networks=['10.0.0.0/8'])])
    assert exc_info.value.code == 'invalid-annotated-type'
    assert "'NetworkConstraints' cannot annotate" in str(exc_info.value)


def test_network_constraints_accept_network_objects_and_normalizes() -> None:
    constraint = NetworkConstraints(
        allowed_networks=[IPv4Network('10.0.0.0/8'), '192.168.0.0/24', IPv4Network('10.0.0.0/8')],
        denied_networks=[IPv6Network('2001:DB8::/32')],
    )
    ta = TypeAdapter(Annotated[IPvAnyAddress, constraint])
    # de-duplicated equivalent networks still work
    assert ta.validate_python('10.1.2.3') == IPv4Address('10.1.2.3')
    assert ta.validate_python('192.168.0.1') == IPv4Address('192.168.0.1')
    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python('2001:db8::1')
    assert exc_info.value.errors(include_url=False)[0]['type'] == 'ip_address_denied'


def test_network_constraints_normalization_json_schema() -> None:
    ta = TypeAdapter(
        Annotated[
            IPvAnyAddress,
            NetworkConstraints(
                allowed_networks=['10.0.0.0/8', IPv4Network('10.0.0.0/8'), '2001:DB8::/32'],
                denied_networks=['10.1.0.0/16', '10.1.0.0/16'],
            ),
        ]
    )
    assert ta.json_schema() == {
        'type': 'string',
        'format': 'ipvanyaddress',
        'allowedNetworks': ['10.0.0.0/8', '2001:db8::/32'],
        'deniedNetworks': ['10.1.0.0/16'],
    }


@pytest.mark.parametrize(
    'ip_type,address_format,constraints',
    [
        (IPv4Address, 'ipv4', NetworkConstraints(allowed_networks=['10.0.0.0/8'], denied_networks=['10.1.0.0/16'])),
        (IPv6Address, 'ipv6', NetworkConstraints(allowed_networks=['2001:db8::/32'])),
        (IPvAnyAddress, 'ipvanyaddress', NetworkConstraints(denied_networks=['10.0.0.0/8'])),
    ],
)
def test_network_constraints_json_schema_keeps_format(ip_type, address_format, constraints) -> None:
    schema = TypeAdapter(Annotated[ip_type, constraints]).json_schema()
    assert schema['type'] == 'string'
    assert schema['format'] == address_format


def test_network_constraints_json_schema_omits_unset_and_keeps_empty_list() -> None:
    omitted = TypeAdapter(Annotated[IPv4Address, NetworkConstraints()]).json_schema()
    assert omitted == {'type': 'string', 'format': 'ipv4'}

    denied_only = TypeAdapter(Annotated[IPv4Address, NetworkConstraints(denied_networks=['10.0.0.0/8'])]).json_schema()
    assert denied_only == {'type': 'string', 'format': 'ipv4', 'deniedNetworks': ['10.0.0.0/8']}
    assert 'allowedNetworks' not in denied_only

    empty_allowed = TypeAdapter(Annotated[IPv4Address, NetworkConstraints(allowed_networks=[])]).json_schema()
    assert empty_allowed == {'type': 'string', 'format': 'ipv4', 'allowedNetworks': []}


def test_network_constraints_model_json_schema() -> None:
    class Model(BaseModel):
        ip: Annotated[IPv4Address, NetworkConstraints(allowed_networks=['10.0.0.0/8'])]

    properties = Model.model_json_schema()['properties']
    assert properties['ip'] == {
        'type': 'string',
        'format': 'ipv4',
        'allowedNetworks': ['10.0.0.0/8'],
        'title': 'Ip',
    }


def test_network_constraints_serialization() -> None:
    class Model(BaseModel):
        ip: Annotated[IPv4Address, NetworkConstraints(allowed_networks=['10.0.0.0/8'])]

    m = Model(ip='10.0.0.1')
    assert json.loads(m.model_dump_json()) == {'ip': '10.0.0.1'}
    assert m.model_dump() == {'ip': IPv4Address('10.0.0.1')}


def test_network_constraints_hash_equal() -> None:
    options = {'allowed_networks': ['10.0.0.0/8'], 'denied_networks': ['10.1.0.0/16']}
    assert hash(NetworkConstraints(**options)) == hash(NetworkConstraints(**options))
    assert NetworkConstraints(**options) == NetworkConstraints(**options)


@pytest.mark.parametrize(
    'changes',
    [
        {'allowed_networks': ['10.1.0.0/16']},
        {'denied_networks': ['10.2.0.0/16']},
        {'allowed_networks': None},
        {'denied_networks': None},
        {'allowed_networks': []},
    ],
)
def test_network_constraints_hash_inequal(changes) -> None:
    options = {'allowed_networks': ['10.0.0.0/8'], 'denied_networks': ['10.1.0.0/16']}
    assert NetworkConstraints(**options) != NetworkConstraints(**{**options, **changes})
