"""
Serviço de Checkout, Split de Pagamento & Pedidos — DentGo
Domínio: Checkout com trava sanitária, split (4.5% + R$ 9,90) e PIN de entrega.
"""

import random
import uuid
from typing import Any, Dict, List
from src.core.database import get_connection
from src.modules.autenticacao_cro.service import verificar_habilitacao_cirurgica


def criar_pedido(
    comprador_id: str,
    distribuidor_id: str,
    itens: List[Dict[str, Any]],  # [{"produto_id": str, "quantidade": int}]
    modalidade_entrega: str,      # 'FLASH_2H', 'CHEGA_HOJE', 'PROGRAMADO'
    dest_latitude: float,
    dest_longitude: float,
    dest_endereco: str,
    taxa_entrega: float = 18.00,
) -> Dict[str, Any]:
    """
    Executa o checkout com trava sanitaria estrita e split financeiro.
    """
    # 1. Trava Sanitaria de CRO
    if not verificar_habilitacao_cirurgica(comprador_id):
        raise PermissionError("Bloqueio Sanitário: Usuário sem CRO ativo não pode adquirir implantes.")

    if not itens:
        raise ValueError("O pedido deve conter pelo menos 1 item.")

    conn = get_connection()
    try:
        pedido_id = str(uuid.uuid4())
        pin_entrega = f"{random.randint(1000, 9999)}"

        with conn:
            # 2. Calcula total dos produtos e reserva estoque
            total_produtos = 0.0
            itens_processados = []
            marca_referencia = None

            for item in itens:
                prod_id = item["produto_id"]
                qtd = int(item["quantidade"])
                if qtd <= 0:
                    raise ValueError("Quantidade deve ser maior que zero.")

                # Valida que todos os produtos pertencem ao mesmo fabricante/marca
                prod_row = conn.execute(
                    "SELECT marca_id FROM produtos WHERE id = ?", (prod_id,)
                ).fetchone()
                if prod_row:
                    marca_do_item = prod_row["marca_id"]
                    if marca_referencia is None:
                        marca_referencia = marca_do_item
                    elif marca_referencia != marca_do_item:
                        raise ValueError(
                            f"Inconsistência multi-vendor: O produto {prod_id} pertence à marca '{marca_do_item}', "
                            f"enquanto o pedido já contém itens da marca '{marca_referencia}'. "
                            "Pedidos cirúrgicos devem pertencer a um único fabricante."
                        )

                # Consulta preco e estoque no distribuidor
                est = conn.execute(
                    """
                    SELECT preco, quantidade 
                    FROM estoque_distribuidor 
                    WHERE distribuidor_id = ? AND produto_id = ?
                    """,
                    (distribuidor_id, prod_id),
                ).fetchone()

                if not est or est["quantidade"] < qtd:
                    raise ValueError(f"Estoque insuficiente para o produto {prod_id} no distribuidor selecionado.")

                preco_unit = est["preco"]
                subtotal = preco_unit * qtd
                total_produtos += subtotal

                # Decrementa estoque atomicamente
                conn.execute(
                    """
                    UPDATE estoque_distribuidor 
                    SET quantidade = quantidade - ? 
                    WHERE distribuidor_id = ? AND produto_id = ?
                    """,
                    (qtd, distribuidor_id, prod_id),
                )

                itens_processados.append((str(uuid.uuid4()), pedido_id, prod_id, qtd, preco_unit))

            # 3. Regra de Negocio Financeira (Split)
            taxa_servico = 9.90
            total_geral = round(total_produtos + taxa_servico + taxa_entrega, 2)
            take_rate_distribuidor = round(total_produtos * 0.045, 2)  # 4.5% da DentGo
            liquido_distribuidor = round(total_produtos - take_rate_distribuidor, 2)

            # 4. Grava Pedido
            conn.execute(
                """
                INSERT INTO pedidos (
                    id, comprador_id, distribuidor_id, status, modalidade_entrega,
                    taxa_produtos, taxa_servico, taxa_entrega, total,
                    take_rate_distribuidor, pin_entrega,
                    dest_latitude, dest_longitude, dest_endereco
                ) VALUES (?, ?, ?, 'PAGO', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pedido_id,
                    comprador_id,
                    distribuidor_id,
                    modalidade_entrega,
                    total_produtos,
                    taxa_servico,
                    taxa_entrega,
                    total_geral,
                    take_rate_distribuidor,
                    pin_entrega,
                    dest_latitude,
                    dest_longitude,
                    dest_endereco,
                ),
            )

            # 5. Grava Itens do Pedido
            conn.executemany(
                """
                INSERT INTO itens_pedido (id, pedido_id, produto_id, quantidade, preco_unitario)
                VALUES (?, ?, ?, ?, ?)
                """,
                itens_processados,
            )

            return {
                "pedido_id": pedido_id,
                "status": "PAGO",
                "pin_entrega": pin_entrega,
                "financeiro": {
                    "total_produtos": total_produtos,
                    "taxa_servico": taxa_servico,
                    "taxa_entrega": taxa_entrega,
                    "total_geral": total_geral,
                    "comissao_dentgo": take_rate_distribuidor,
                    "repasse_distribuidor": liquido_distribuidor,
                },
                "modalidade": modalidade_entrega,
            }
    finally:
        conn.close()


def obter_pedido(pedido_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
        if not row:
            return None
        res = dict(row)
        itens = conn.execute(
            """
            SELECT i.*, p.nome, p.sku 
            FROM itens_pedido i 
            JOIN produtos p ON i.produto_id = p.id 
            WHERE i.pedido_id = ?
            """,
            (pedido_id,),
        ).fetchall()
        res["itens"] = [dict(i) for i in itens]
        return res
    finally:
        conn.close()
