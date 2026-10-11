"""
Motor de Compatibilidade & Catálogo Canônico — DentGo
Domínio cirúrgico e protético puro (zero stubs, 100% determinístico).
"""

import math
from typing import Any, Dict, List, Optional
from src.core.database import get_connection


def listar_marcas() -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT id, nome, slug FROM marcas WHERE ativo = 1 ORDER BY nome ASC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def seed_marcas_canonicas() -> None:
    marcas = [
        ("straumann", "Straumann", "straumann"),
        ("neodent", "Neodent", "neodent"),
        ("conexao", "Conexão Implantes", "conexao-implantes"),
        ("sin", "S.I.N. Implant System", "sin"),
        ("dsp", "DSP Biomedical", "dsp-biomedical"),
        ("titaniumfix", "Titanium Fix", "titanium-fix"),
        ("intraoss", "Intraoss", "intraoss"),
        ("dentoflex", "Dentoflex", "dentoflex"),
        ("plenum", "Plenum", "plenum"),
        ("fgm", "FGM Dental Group", "fgm"),
    ]
    conn = get_connection()
    with conn:
        for m_id, nome, slug in marcas:
            conn.execute(
                "INSERT OR IGNORE INTO marcas (id, nome, slug) VALUES (?, ?, ?)",
                (m_id, nome, slug),
            )
    conn.close()


def buscar_produtos_cirurgicos(
    tipo_conexao: Optional[str] = None,   # 'CM', 'HE', 'HI'
    marca_id: Optional[str] = None,
    categoria: Optional[str] = None,      # 'implante', 'munhao', 'mini_pilar', etc.
    diametro: Optional[float] = None,
    comprimento: Optional[float] = None,
    angulacao: Optional[float] = None,
    apenas_disponiveis: bool = True,
    limite: int = 50,
) -> List[Dict[str, Any]]:
    """
    Busca cirúrgica facetada de precisão milimétrica.
    """
    conn = get_connection()
    try:
        query = """
            SELECT 
                p.id, p.nome, p.tipo, p.sku, p.categoria,
                p.diametro, p.comprimento, p.altura_cinta, p.angulacao,
                p.imagem_url,
                m.id as marca_id, m.nome as marca_nome,
                c.tipo as conexao_tipo, c.descricao as conexao_descricao,
                COALESCE(MIN(e.preco), 0.0) as menor_preco,
                COALESCE(SUM(e.quantidade), 0) as estoque_total,
                MAX(e.disponivel_flash) as pronta_entrega_2h
            FROM produtos p
            JOIN marcas m ON p.marca_id = m.id
            JOIN conexoes_proteticas c ON p.conexao_id = c.id
            LEFT JOIN estoque_distribuidor e ON p.id = e.produto_id
            WHERE p.ativo = 1
        """
        params: List[Any] = []

        if tipo_conexao:
            query += " AND c.tipo = ?"
            params.append(tipo_conexao.upper())
        if marca_id:
            query += " AND m.id = ?"
            params.append(marca_id)
        if categoria:
            query += " AND p.categoria = ?"
            params.append(categoria)
        if diametro is not None:
            query += " AND p.diametro = ?"
            params.append(diametro)
        if comprimento is not None:
            query += " AND p.comprimento = ?"
            params.append(comprimento)
        if angulacao is not None:
            query += " AND p.angulacao = ?"
            params.append(angulacao)

        query += " GROUP BY p.id"

        if apenas_disponiveis:
            query += " HAVING estoque_total > 0"

        query += " ORDER BY p.nome ASC LIMIT ?"
        params.append(limite)

        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def calcular_distancia_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula a distancia fisica em KM entre o consultorio e o distribuidor."""
    r = 6371.0  # Raio da Terra em km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def buscar_distribuidores_proximos_com_estoque(
    produto_id: str,
    cliente_lat: float,
    cliente_lon: float,
    raio_km: float = 25.0,
) -> List[Dict[str, Any]]:
    """
    Localiza os distribuidores com estoque real ordenados por proximidade.
    """
    conn = get_connection()
    try:
        query = """
            SELECT 
                d.id, d.nome_fantasia, d.razao_social, d.cnpj,
                d.afe_anvisa, d.latitude, d.longitude, d.whatsapp,
                e.preco, e.quantidade, e.disponivel_flash
            FROM estoque_distribuidor e
            JOIN distribuidores d ON e.distribuidor_id = d.id
            WHERE e.produto_id = ? AND e.quantidade > 0 AND d.ativo = 1
        """
        rows = conn.execute(query, (produto_id,)).fetchall()
        resultados = []
        for r in rows:
            distrib = dict(r)
            dist_km = calcular_distancia_haversine(
                cliente_lat, cliente_lon, distrib["latitude"], distrib["longitude"]
            )
            if dist_km <= raio_km:
                distrib["distancia_km"] = round(dist_km, 2)
                # Estimativa de tempo em minutos para SP (media 25 km/h transito urbano)
                distrib["eta_minutos"] = max(20, int((dist_km / 25.0) * 60) + 15)
                resultados.append(distrib)

        resultados.sort(key=lambda x: x["distancia_km"])
        return resultados
    finally:
        conn.close()
