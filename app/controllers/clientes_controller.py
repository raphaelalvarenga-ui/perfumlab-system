from app.database.json_storage import (
    DATABASE_PATH,
    buscar_por_id,
    cargar_tabla,
    coincide_texto,
    es_activo,
    fecha_actual,
    guardar_tabla,
    inicializar_datos_json,
    siguiente_id,
)
from app.models.cliente import Cliente
from app.validaciones import validar_id_positivo


class ClientesController:
    def __init__(self, ruta_db=DATABASE_PATH):
        self.ruta_datos = ruta_db
        inicializar_datos_json(self.ruta_datos)

    def crear_cliente(self, cliente):
        cliente.validar()
        clientes = cargar_tabla("clientes", self.ruta_datos)

        if self._existe_correo_cliente(clientes, cliente.correo):
            raise ValueError("El correo ya esta registrado.")

        cliente_id = siguiente_id("clientes", clientes)
        clientes.append(self._crear_registro_cliente(cliente_id, cliente))
        guardar_tabla("clientes", clientes, self.ruta_datos)
        return cliente_id

    def obtener_cliente(self, cliente_id):
        cliente_id = validar_id_positivo(cliente_id, "cliente")
        clientes = cargar_tabla("clientes", self.ruta_datos)
        cliente = buscar_por_id(clientes, cliente_id)
        return Cliente.desde_fila(cliente) if cliente else None

    def listar_clientes(self, incluir_inactivos=False):
        clientes = cargar_tabla("clientes", self.ruta_datos)

        if not incluir_inactivos:
            clientes = [cliente for cliente in clientes if es_activo(cliente)]

        clientes.sort(key=lambda cliente: str(cliente.get("nombre", "")).lower())
        return [Cliente.desde_fila(cliente) for cliente in clientes]

    def buscar_clientes(self, texto, incluir_inactivos=False):
        texto = texto.strip()
        clientes = cargar_tabla("clientes", self.ruta_datos)

        if not incluir_inactivos:
            clientes = [cliente for cliente in clientes if es_activo(cliente)]

        clientes = [
            cliente
            for cliente in clientes
            if (
                coincide_texto(cliente.get("nombre"), texto)
                or coincide_texto(cliente.get("correo"), texto)
                or coincide_texto(cliente.get("telefono"), texto)
            )
        ]
        clientes.sort(key=lambda cliente: str(cliente.get("nombre", "")).lower())
        return [Cliente.desde_fila(cliente) for cliente in clientes]

    def actualizar_cliente(self, cliente_id, cliente):
        cliente_id = validar_id_positivo(cliente_id, "cliente")
        cliente.validar()
        clientes = cargar_tabla("clientes", self.ruta_datos)
        registro = buscar_por_id(clientes, cliente_id)

        if registro is None:
            return False

        if self._existe_correo_cliente(clientes, cliente.correo, excluir_id=cliente_id):
            raise ValueError("El correo ya esta registrado.")

        registro.update(
            {
                "nombre": cliente.nombre.strip(),
                "correo": cliente.correo.strip().lower(),
                "telefono": cliente.telefono.strip(),
                "direccion": cliente.direccion.strip(),
                "activo": int(cliente.activo),
                "fecha_actualizacion": fecha_actual(),
            }
        )
        guardar_tabla("clientes", clientes, self.ruta_datos)
        return True

    def eliminar_cliente(self, cliente_id):
        cliente_id = validar_id_positivo(cliente_id, "cliente")
        clientes = cargar_tabla("clientes", self.ruta_datos)
        registro = buscar_por_id(clientes, cliente_id)

        if registro is None:
            return False

        registro["activo"] = 0
        registro["fecha_actualizacion"] = fecha_actual()
        guardar_tabla("clientes", clientes, self.ruta_datos)
        return True

    def _crear_registro_cliente(self, cliente_id, cliente):
        return {
            "id": cliente_id,
            "nombre": cliente.nombre.strip(),
            "correo": cliente.correo.strip().lower(),
            "telefono": cliente.telefono.strip(),
            "direccion": cliente.direccion.strip(),
            "activo": int(cliente.activo),
            "fecha_creacion": fecha_actual(),
            "fecha_actualizacion": None,
        }

    def _existe_correo_cliente(self, clientes, correo, excluir_id=None):
        correo = correo.strip().lower()
        excluir_id = int(excluir_id) if excluir_id is not None else None

        return any(
            str(cliente.get("correo") or "").strip().lower() == correo
            and int(cliente["id"]) != excluir_id
            for cliente in clientes
            if str(cliente.get("correo") or "").strip()
        )
