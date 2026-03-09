import pytest

from apps.ticket_printer.services.zpl_service import ZPLGenerator
from tests.factories import OrderFactory


@pytest.mark.unit
@pytest.mark.django_db
class TestZPLGenerator:
    def test_generate_label(self):
        # Arrange — usa o model Order refatorado com related Customer + Address
        order = OrderFactory(picking="PCK-123")
        # Atualiza o endereço do cliente para valores conhecidos
        addr = order.customer.address
        addr.street = "Rua ABC"
        addr.number = "123"
        addr.district = "Centro"
        addr.city = "São Paulo"
        addr.state = "SP"
        addr.zip_code = "01000000"
        addr.save()

        volume_num = 1
        total_volumes = 2

        # Act
        zpl = ZPLGenerator.generate_label(order, volume_num, total_volumes)

        # Assert
        assert "^XA" in zpl
        assert "^XZ" in zpl
        assert "Picking: PCK-123" in zpl
        assert "Rua ABC" in zpl
        assert "123" in zpl
        assert "Centro" in zpl
        assert "São Paulo" in zpl
        assert "SP" in zpl
        assert "Vol: 1/2" in zpl
