"""
Serviço de Telemetria & Rastreamento em Tempo Real — DentGo
Domínio: Mapa ao vivo, cálculo de trajeto, atualização de status e PIN de entrega.
"""

from typing import Any, Dict, Optional
from src.core.database import get_connection
from src.modules.catalogo_compatibilidade.service import calcular_distancia_haversine


STATUS_FLUXO = [
    "CRIADO",
    "PAGO",
    "SEPARANDO",
    "DESPACHADO",
    "EM_ROTA",
    "ENTREGUE",
    "CANCELADO",
]


def atualizar_status_pedido(pedido_id: str, novo_status: str) -> Dict[str, Any]:
    if novo_status not in STATUS_FLUXO:
        raise ValueError(f"Status invalido: {novo_status}")

    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "UPDATE pedidos SET status = ? WHERE id = ?",
                (novo_status, pedido_id),
            )
        row = conn.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
        if not row:
            raise KeyError(f"Pedido {pedido_id} nao encontrado.")
        return dict(row)
    finally:
        conn.close()


def obter_telemetria_entrega(pedido_id: str, motoboy_lat: Optional[float] = None, motoboy_lon: Optional[float] = None) -> Dict[str, Any]:
    """
    Retorna telemetria completa da entrega para renderização no mapa estilo Uber/Glovo.
    """
    conn = get_connection()
    try:
        pedido = conn.execute(
            """
            SELECT p.*, d.nome_fantasia as distribuidor_nome, d.latitude as origem_lat, d.longitude as origem_lon
            FROM pedidos p
            JOIN distribuidores d ON p.distribuidor_id = d.id
            WHERE p.id = ?
            """,
            (pedido_id,),
        ).fetchone()

        if not pedido:
            raise KeyError(f"Pedido {pedido_id} nao encontrado.")

        ped_data = dict(pedido)
        origem = {"lat": ped_data["origem_lat"], "lon": ped_data["origem_lon"]}
        destino = {"lat": ped_data["dest_latitude"], "lon": ped_data["dest_longitude"], "endereco": ped_data["dest_endereco"]}

        # Se motoboy_lat/lon nao informado, usa o ponto medio ou a origem
        pos_atual_lat = motoboy_lat if motoboy_lat is not None else (origem["lat"] + destino["lat"]) / 2
        pos_atual_lon = motoboy_lon if motoboy_lon is not None else (origem["lon"] + destino["lon"]) / 2

        distancia_restante_km = calcular_distancia_haversine(
            pos_atual_lat, pos_atual_lon, destino["lat"], destino["lon"]
        )
        eta_minutos = max(5, int((distancia_restante_km / 25.0) * 60))

        return {
            "pedido_id": pedido_id,
            "status": ped_data["status"],
            "modalidade": ped_data["modalidade_entrega"],
            "pin_entrega": ped_data["pin_entrega"],
            "distribuidor": ped_data["distribuidor_nome"],
            "origem": origem,
            "destino": destino,
            "motoboy_posicao_atual": {"lat": pos_atual_lat, "lon": pos_atual_lon},
            "distancia_restante_km": round(distancia_restante_km, 2),
            "eta_minutos": eta_minutos,
        }
    finally:
        conn.close()


def confirmar_entrega_com_pin(pedido_id: str, pin_informado: str) -> bool:
    """Valida o código PIN de 4 dígitos informado ao motoboy."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT pin_entrega FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
        if not row:
            return False
        if row["pin_entrega"] == pin_informado.strip():
            with conn:
                conn.execute("UPDATE pedidos SET status = 'ENTREGUE' WHERE id = ?", (pedido_id,))
            return True
        return False
    finally:
        conn.close()
