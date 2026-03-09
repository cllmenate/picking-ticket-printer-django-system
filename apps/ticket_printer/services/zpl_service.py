class ZPLGenerator:
    @staticmethod
    def generate_label(order, volume_num: int, total_volumes: int) -> str:
        """
        Gera a string ZPL para a etiqueta do volume especificado para o pedido.
        """
        # Endereço formatado em duas partes para melhor legibilidade
        addr_main = []
        address = (
            order.customer.address
            if order.customer and order.customer.address
            else None
        )

        if address and address.street:
            addr_main.append(address.street)
        if address and address.number:
            addr_main.append(f"{address.number}")
        if address and address.district:
            addr_main.append(f"- {address.district}")

        addr_sub = []
        city_uf = []
        if address and address.city:
            city_uf.append(address.city)
        if address and address.state:
            city_uf.append(address.state)
        if city_uf:
            addr_sub.append(" / ".join(city_uf))
        if address and address.zip_code:
            addr_sub.append(f"CEP: {address.zip_code}")

        street_num = (
            f"{address.street or ''}, {address.number or ''}"
            if address
            else ""
        )
        district = address.district if address else ""
        city_state_zip = (
            f"{address.city or ''}/ {address.state or ''} - {address.zip_code or ''}"
            if address
            else ""
        )

        zpl = f"""^XA
            ^CI28

            ^CF0,60,60
            ^FO40,25^FDPicking: {order.picking}^FS

            ^FO40,85^GB720,3,3^FS

            ^CF0,35,35
            ^FO40,110^FD{order.customer.name if order.customer else ""}^FS

            ^CF0,35,35
            ^FO40,160^FD{street_num}^FS

            ^CF0,60,60
            ^FO40,200^FD{district}^FS

            ^CF0,35,35
            ^FO40,270^FD{city_state_zip}^FS

            ^FO40,325^GB720,3,3^FS

            ^CF0,60,60
            ^FO0,350^FB800,1,0,C^FDVol: {volume_num}/{total_volumes}^FS

        ^XZ"""  # noqa: E501
        return zpl
