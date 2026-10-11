"""
Serviço do Radar Odonto & Clipping Editorial — DentGo
Domínio: O "Jornal Vivo" interativo com clipping diário e fontes em 1 clique.
"""

import uuid
from typing import Any, Dict, List, Optional
from src.core.database import get_connection


def publicar_noticia(
    titulo: str,
    resumo: str,
    fonte_nome: str,
    fonte_url: str,
    categoria: str,  # 'LANCAMENTO', 'ESTUDO', 'MERCADO', 'RECALL'
    data_publicacao: str,
    marca_relacionada: Optional[str] = None,
) -> Dict[str, Any]:
    conn = get_connection()
    try:
        noticia_id = str(uuid.uuid4())
        with conn:
            conn.execute(
                """
                INSERT INTO radar_noticias (
                    id, titulo, resumo, fonte_nome, fonte_url,
                    categoria, data_publicacao, marca_relacionada
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    noticia_id,
                    titulo.strip(),
                    resumo.strip(),
                    fonte_nome.strip(),
                    fonte_url.strip(),
                    categoria.upper(),
                    data_publicacao,
                    marca_relacionada,
                ),
            )
            row = conn.execute("SELECT * FROM radar_noticias WHERE id = ?", (noticia_id,)).fetchone()
            return dict(row)
    finally:
        conn.close()


def listar_radar_noticias(
    categoria: Optional[str] = None,
    marca: Optional[str] = None,
    limite: int = 20,
) -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        query = "SELECT * FROM radar_noticias WHERE 1=1"
        params: List[Any] = []
        if categoria:
            query += " AND categoria = ?"
            params.append(categoria.upper())
        if marca:
            query += " AND marca_relacionada = ?"
            params.append(marca)

        query += " ORDER BY data_publicacao DESC LIMIT ?"
        params.append(limite)

        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def seed_noticias_iniciais() -> None:
    conn = get_connection()
    try:
        qtd = conn.execute("SELECT COUNT(*) as total FROM radar_noticias").fetchone()["total"]
        if qtd > 0:
            return
        noticias = [
            (
                "Nova Linha de Scan Bodies Conexão In-Lego Homologada para Exocad",
                "Conexão Implantes libera biblioteca digital oficial com precisão de 5 microns para escaneamento intraoral.",
                "Portal Dental Press",
                "https://dentalpress.com.br/noticias/conexao-in-lego",
                "LANCAMENTO",
                "2026-10-10",
                "conexao",
            ),
            (
                "Estudo de 10 Anos Comprova Alta Estabilidade em Implantes Cone Morse",
                "Artigo publicado no JOMI demonstra 98.7% de taxa de sobrevivência em reabilitações unitárias com carga imediata.",
                "PubMed / JOMI",
                "https://pubmed.ncbi.nlm.nih.gov/3829102",
                "ESTUDO",
                "2026-10-09",
                "straumann",
            ),
            (
                "Mercado Odontológico Nacional Cresce 14% Puxado por Fluxo Digital",
                "Pesquisa aponta avanço maciço de cirurgia guiada e scanners 3D nos consultórios da Grande São Paulo.",
                "Valor Econômico",
                "https://valor.globo.com/empresas/noticia/odonto-digital-2026",
                "MERCADO",
                "2026-10-08",
                None,
            ),
        ]
        with conn:
            for tit, res, fn, fu, cat, dt, mr in noticias:
                conn.execute(
                    """
                    INSERT INTO radar_noticias (
                        id, titulo, resumo, fonte_nome, fonte_url,
                        categoria, data_publicacao, marca_relacionada
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (str(uuid.uuid4()), tit, res, fn, fu, cat, dt, mr),
                )
    finally:
        conn.close()
