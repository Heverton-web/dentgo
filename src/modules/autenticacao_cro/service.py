"""
Serviço de Autenticação e Validação Sanitária CRO — DentGo
Domínio: Verificação profissional obrigatória para compra cirúrgica.
"""

import re
import uuid
from typing import Any, Dict, Optional
from src.core.database import get_connection

UFS_VALIDAS = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
    "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
    "RS", "RO", "RR", "SC", "SP", "SE", "TO"
}


def validar_formato_cro(cro_numero: str, cro_uf: str) -> bool:
    """Valida se o formato do CRO e a UF sao validos no padrao CFO."""
    if not cro_numero or not cro_uf:
        return False
    uf = cro_uf.strip().upper()
    if uf not in UFS_VALIDAS:
        return False
    # CRO numero contem entre 3 e 7 digitos
    num_limpo = re.sub(r"\D", "", cro_numero)
    return 3 <= len(num_limpo) <= 7


def cadastrar_comprador(
    nome: str,
    email: str,
    cpf: str,
    cro_numero: str,
    cro_uf: str,
    whatsapp: str,
    tipo_usuario: str = "DENTISTA",
) -> Dict[str, Any]:
    """Cadastra ou atualiza um dentista/laboratorio com status de CRO."""
    if not validar_formato_cro(cro_numero, cro_uf):
        raise ValueError(f"CRO invalido: {cro_numero}/{cro_uf}")

    cpf_limpo = re.sub(r"\D", "", cpf)
    if len(cpf_limpo) != 11:
        raise ValueError("CPF invalido: deve conter 11 digitos")

    conn = get_connection()
    try:
        user_id = str(uuid.uuid4())
        # Na integracao de producao, consulta API do CFO. No core deterministico, CRO no formato valido nasce ATIVO
        status_cro = "ATIVO"
        with conn:
            conn.execute(
                """
                INSERT INTO usuarios (id, nome, email, cpf, cro_numero, cro_uf, cro_status, tipo_usuario, whatsapp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(email) DO UPDATE SET
                    nome=excluded.nome,
                    cro_numero=excluded.cro_numero,
                    cro_uf=excluded.cro_uf,
                    cro_status=excluded.cro_status,
                    whatsapp=excluded.whatsapp
                """,
                (
                    user_id,
                    nome.strip(),
                    email.strip().lower(),
                    cpf_limpo,
                    cro_numero.strip(),
                    cro_uf.strip().upper(),
                    status_cro,
                    tipo_usuario,
                    whatsapp.strip(),
                ),
            )
            row = conn.execute("SELECT * FROM usuarios WHERE email = ?", (email.strip().lower(),)).fetchone()
            return dict(row)
    finally:
        conn.close()


def verificar_habilitacao_cirurgica(usuario_id: str) -> bool:
    """Verifica se o comprador possui CRO ativo para compra de implantes."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT cro_status FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
        if not row:
            return False
        return row["cro_status"] == "ATIVO"
    finally:
        conn.close()
