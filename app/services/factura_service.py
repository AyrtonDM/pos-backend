import secrets
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from xml.etree import ElementTree

from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.clientes import Cliente
from app.models.empresas import Caja, CajaSesion, Sucursal
from app.models.ventas import DetalleVenta
from app.models.ventas import Factura
from app.models.ventas import Venta
from app.models.usuarios import Usuario
from app.repositories.empresa_repository import EmpresaRepository
from app.schemas.factura_schema import (
    FacturaDetalleResponse,
    FacturaListadoResponse,
    FacturaVentaResponse,
    ReenviarFacturaResponse,
)
from app.utils.email_service import send_invoice_email


class FacturaService:
    APP_DIR = Path(__file__).resolve().parents[1]
    XML_DIR = APP_DIR / "XMLS"
    PDF_DIR = XML_DIR / "PDFS"

    @staticmethod
    def reenviar_factura_empresa(
        db: Session,
        current_user,
        id_empresa: int,
        id_factura: int,
    ) -> ReenviarFacturaResponse:
        empresa = EmpresaRepository.obtener_empresa_por_usuario(
            db=db,
            id_usuario=current_user.id_usuario,
            id_empresa=id_empresa,
        )
        if empresa is None:
            raise LookupError("Empresa no encontrada para este usuario.")

        factura = (
            db.query(Factura)
            .join(Factura.venta)
            .join(Venta.caja_sesion)
            .join(CajaSesion.caja)
            .join(Caja.sucursal)
            .options(
                joinedload(Factura.venta)
                .joinedload(Venta.cliente)
                .joinedload(Cliente.usuario)
                .joinedload(Usuario.persona)
            )
            .filter(
                Factura.id_factura == id_factura,
                Sucursal.id_empresa == id_empresa,
            )
            .first()
        )
        if factura is None:
            raise LookupError("Factura no encontrada para esta empresa.")

        cliente = factura.venta.cliente
        if cliente is None or cliente.usuario is None:
            raise ValueError("La factura no tiene un cliente con usuario asociado.")

        ruta_relativa = Path(factura.pdf_generado)
        ruta_pdf = (FacturaService.APP_DIR / ruta_relativa).resolve()
        pdf_dir = FacturaService.PDF_DIR.resolve()
        if pdf_dir not in ruta_pdf.parents:
            raise ValueError("La ruta del PDF de la factura no es valida.")
        if not ruta_pdf.is_file():
            raise LookupError("No se encontro el PDF generado de la factura.")

        enviado = FacturaService.enviar_factura(
            cliente=cliente,
            factura=factura,
            ruta_pdf=ruta_pdf,
        )
        if not enviado:
            raise RuntimeError("No se pudo enviar la factura por correo.")

        return ReenviarFacturaResponse(
            mensaje="Factura reenviada correctamente.",
            id_factura=factura.id_factura,
            correo_cliente=cliente.usuario.email,
            enviado=True,
        )

    @staticmethod
    def listar_facturas_empresa(
        db: Session,
        current_user,
        id_empresa: int,
    ) -> list[FacturaListadoResponse]:
        empresa = EmpresaRepository.obtener_empresa_por_usuario(
            db=db,
            id_usuario=current_user.id_usuario,
            id_empresa=id_empresa,
        )
        if empresa is None:
            raise LookupError("Empresa no encontrada para este usuario.")

        facturas = (
            db.query(Factura)
            .join(Factura.venta)
            .join(Venta.caja_sesion)
            .join(CajaSesion.caja)
            .join(Caja.sucursal)
            .options(
                joinedload(Factura.venta)
                .joinedload(Venta.cliente)
                .joinedload(Cliente.usuario)
                .joinedload(Usuario.persona),
                joinedload(Factura.venta).joinedload(Venta.tipo_venta),
                joinedload(Factura.venta)
                .selectinload(Venta.detalles)
                .joinedload(DetalleVenta.producto),
            )
            .filter(Sucursal.id_empresa == id_empresa)
            .order_by(Factura.fecha_emision.desc(), Factura.id_factura.desc())
            .all()
        )

        resultado = []
        for factura in facturas:
            venta = factura.venta
            cliente = venta.cliente
            nombre_cliente = (
                cliente.usuario.persona.nombre_completo
                if cliente and cliente.usuario and cliente.usuario.persona
                else "Sin nombre"
            )
            detalles = [
                FacturaDetalleResponse(
                    id_detalle_venta=detalle.id_detalle_venta,
                    id_producto=detalle.id_producto,
                    producto=detalle.producto.nombre if detalle.producto else "Sin producto",
                    cantidad=detalle.cantidad,
                    precio_unitario=detalle.precio_unitario,
                    descuento=detalle.descuento,
                    subtotal=detalle.subtotal,
                    total=detalle.total,
                    descripcion=detalle.descripcion,
                )
                for detalle in venta.detalles
            ]
            venta_response = FacturaVentaResponse(
                id_venta=venta.id_venta,
                id_tipo_venta=venta.id_tipo_venta,
                id_cliente=venta.id_cliente,
                id_caja_sesion=venta.id_caja_sesion,
                id_usuario=venta.id_usuario,
                subtotal=venta.subtotal,
                descuento_total=venta.descuento_total,
                total=venta.total,
                fecha=venta.fecha,
                estado=venta.estado,
                detalles=detalles,
            )
            resultado.append(
                FacturaListadoResponse(
                    id_factura=factura.id_factura,
                    id_venta=factura.id_venta,
                    nit_emisor=factura.nit_emisor,
                    numero_factura=factura.numero_factura,
                    fecha_emision=factura.fecha_emision,
                    nit_cliente=factura.nit_cliente,
                    nombre_cliente=nombre_cliente,
                    monto_total=factura.monto_total,
                    iva=factura.iva,
                    cufd=factura.cufd,
                    cuf=factura.cuf,
                    xml_generado=factura.xml_generado,
                    pdf_generado=factura.pdf_generado,
                    venta=venta_response,
                )
            )
        return resultado

    @staticmethod
    def _generar_codigo_fiscal() -> str:
        return secrets.token_hex(28).upper()

    @staticmethod
    def _formatear_decimal(valor) -> str:
        return str(Decimal(valor or 0).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    @staticmethod
    def _crear_xml(factura: Factura, detalles: list[dict], ruta: Path) -> None:
        raiz = ElementTree.Element("factura")
        campos = (
            ("nitEmisor", factura.nit_emisor),
            ("numeroFactura", factura.numero_factura),
            ("fechaEmision", factura.fecha_emision.isoformat(timespec="milliseconds")),
            ("nitCliente", factura.nit_cliente),
            ("montoTotal", FacturaService._formatear_decimal(factura.monto_total)),
            ("iva", FacturaService._formatear_decimal(factura.iva)),
            ("cuf", factura.cuf),
            ("cufd", factura.cufd),
        )
        for nombre, valor in campos:
            ElementTree.SubElement(raiz, nombre).text = str(valor)

        detalles_elemento = ElementTree.SubElement(raiz, "detalles")
        for detalle in detalles:
            detalle_elemento = ElementTree.SubElement(detalles_elemento, "detalle")
            ElementTree.SubElement(detalle_elemento, "idProducto").text = str(
                detalle["id_producto"]
            )
            ElementTree.SubElement(detalle_elemento, "producto").text = str(
                detalle["producto"]
            )
            ElementTree.SubElement(detalle_elemento, "cantidad").text = str(
                detalle["cantidad"]
            )
            ElementTree.SubElement(detalle_elemento, "subtotal").text = (
                FacturaService._formatear_decimal(detalle["subtotal"])
            )

        arbol = ElementTree.ElementTree(raiz)
        ElementTree.indent(arbol, space="    ")
        arbol.write(ruta, encoding="utf-8", xml_declaration=True)

    @staticmethod
    def _crear_pdf(
        factura: Factura,
        empresa_nombre: str,
        cliente_nombre: str,
        detalles: list[dict],
        ruta: Path,
    ) -> None:
        ancho, alto = 1240, 1754
        margen = 70
        fuente = ImageFont.load_default(size=24)
        fuente_titulo = ImageFont.load_default(size=38)
        fuente_tabla = ImageFont.load_default(size=21)
        paginas: list[Image.Image] = []

        def nueva_pagina() -> tuple[Image.Image, ImageDraw.ImageDraw, int]:
            imagen = Image.new("RGB", (ancho, alto), "white")
            dibujo = ImageDraw.Draw(imagen)
            return imagen, dibujo, margen

        imagen, dibujo, y = nueva_pagina()
        dibujo.text((margen, y), f"FACTURA N. {factura.numero_factura}", fill="black", font=fuente_titulo)
        y += 70
        encabezado = [
            f"Empresa: {empresa_nombre}",
            f"NIT emisor: {factura.nit_emisor}",
            f"Cliente: {cliente_nombre}",
            f"NIT/Codigo cliente: {factura.nit_cliente}",
            f"Fecha: {factura.fecha_emision.isoformat(timespec='seconds')}",
            f"CUF: {factura.cuf}",
            f"CUFD: {factura.cufd}",
        ]
        for linea in encabezado:
            dibujo.text((margen, y), linea, fill="black", font=fuente)
            y += 42

        y += 25
        columnas = (margen, 230, 720, 900)
        dibujo.rectangle((margen, y, ancho - margen, y + 55), outline="black", width=2)
        for x, titulo in zip(columnas, ("ID", "Producto", "Cantidad", "Subtotal")):
            dibujo.text((x + 8, y + 13), titulo, fill="black", font=fuente_tabla)
        y += 55

        for detalle in detalles:
            if y + 55 > alto - 180:
                paginas.append(imagen)
                imagen, dibujo, y = nueva_pagina()
                dibujo.text((margen, y), "Detalle de factura (continuacion)", fill="black", font=fuente_titulo)
                y += 75

            dibujo.rectangle((margen, y, ancho - margen, y + 55), outline="black", width=1)
            valores = (
                detalle["id_producto"],
                str(detalle["producto"])[:35],
                detalle["cantidad"],
                FacturaService._formatear_decimal(detalle["subtotal"]),
            )
            for x, valor in zip(columnas, valores):
                dibujo.text((x + 8, y + 13), str(valor), fill="black", font=fuente_tabla)
            y += 55

        y += 35
        dibujo.text(
            (margen, y),
            f"Total: {FacturaService._formatear_decimal(factura.monto_total)}",
            fill="black",
            font=fuente_titulo,
        )
        y += 55
        dibujo.text(
            (margen, y),
            f"IVA (13%): {FacturaService._formatear_decimal(factura.iva)}",
            fill="black",
            font=fuente,
        )
        paginas.append(imagen)
        try:
            paginas[0].save(
                ruta,
                "PDF",
                resolution=150.0,
                save_all=True,
                append_images=paginas[1:],
            )
        finally:
            for pagina in paginas:
                pagina.close()

    @staticmethod
    def crear_factura(
        db: Session,
        venta,
        cliente,
        empresa,
        detalles: list[dict],
    ) -> tuple[Factura, Path]:
        FacturaService.XML_DIR.mkdir(parents=True, exist_ok=True)
        FacturaService.PDF_DIR.mkdir(parents=True, exist_ok=True)

        fecha_emision = datetime.now()
        monto_total = Decimal(venta.total)
        iva = (monto_total * Decimal("0.13")).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        factura = Factura(
            id_venta=venta.id_venta,
            nit_emisor=empresa.nit,
            numero_factura=0,
            fecha_emision=fecha_emision,
            nit_cliente=cliente.codigo_cliente,
            monto_total=monto_total,
            iva=iva,
            cufd=FacturaService._generar_codigo_fiscal(),
            cuf=FacturaService._generar_codigo_fiscal(),
            xml_generado="",
            pdf_generado="",
        )
        db.add(factura)
        db.flush()

        factura.numero_factura = factura.id_factura
        nombre_base = f"factura_{factura.id_factura}"
        ruta_xml = FacturaService.XML_DIR / f"{nombre_base}.xml"
        ruta_pdf = FacturaService.PDF_DIR / f"{nombre_base}.pdf"

        FacturaService._crear_xml(factura=factura, detalles=detalles, ruta=ruta_xml)
        FacturaService._crear_pdf(
            factura=factura,
            empresa_nombre=empresa.nombre,
            cliente_nombre=cliente.usuario.persona.nombre_completo,
            detalles=detalles,
            ruta=ruta_pdf,
        )

        factura.xml_generado = str(ruta_xml.relative_to(FacturaService.APP_DIR))
        factura.pdf_generado = str(ruta_pdf.relative_to(FacturaService.APP_DIR))
        db.flush()
        return factura, ruta_pdf

    @staticmethod
    def enviar_factura(cliente, factura: Factura, ruta_pdf: Path) -> bool:
        return send_invoice_email(
            email=cliente.usuario.email,
            nombre=cliente.usuario.persona.nombre_completo,
            numero_factura=factura.numero_factura,
            pdf_path=ruta_pdf,
        )
