"""
Servidor HTTP Completo e Unificado — DentGo
Padrão-Ouro Canônico: Python Puro, 100% Determinístico, Zero Stubs.
OpenAPI 3.1 + Swagger Studio + Rotas de Domínio (Catálogo, Auth, Checkout, Tracking, Radar).
Lei Inviolável #11 do Ecossistema AIDD.
"""

import json
import pathlib
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict
from src.core.database import init_db
from src.modules.catalogo_compatibilidade.service import (
    listar_marcas,
    buscar_produtos_cirurgicos,
    buscar_distribuidores_proximos_com_estoque,
    seed_marcas_canonicas,
)
from src.modules.autenticacao_cro.service import cadastrar_comprador
from src.modules.checkout_split.service import criar_pedido, obter_pedido
from src.modules.telemetria_logistica.service import (
    obter_telemetria_entrega,
    confirmar_entrega_com_pin,
)
from src.modules.radar_noticias.service import (
    listar_radar_noticias,
    seed_noticias_iniciais,
)

OPENAPI_SPEC = {
    "openapi": "3.1.0",
    "info": {
        "title": "DentGo API — Marketplace Cirúrgico & On-Demand Delivery",
        "version": "1.0.0",
        "description": "API Padrão-Ouro Soberana para pronta-entrega cirúrgica, componentes protéticos e tracking em tempo real.",
    },
    "paths": {
        "/api/saude": {
            "get": {"summary": "Healthcheck e telemetria", "responses": {"200": {"description": "OK"}}}
        },
        "/api/marcas": {
            "get": {"summary": "Lista as 10 marcas homologadas", "responses": {"200": {"description": "OK"}}}
        },
        "/api/produtos": {
            "get": {
                "summary": "Busca cirúrgica de precisão milimétrica",
                "parameters": [
                    {"name": "conexao", "in": "query", "schema": {"type": "string"}},
                    {"name": "categoria", "in": "query", "schema": {"type": "string"}},
                    {"name": "diametro", "in": "query", "schema": {"type": "number"}},
                ],
                "responses": {"200": {"description": "Produtos filtrados"}},
            }
        },
        "/api/distribuidores/proximos": {
            "get": {
                "summary": "Localiza distribuidores próximos com estoque",
                "parameters": [
                    {"name": "produto_id", "in": "query", "required": True, "schema": {"type": "string"}},
                    {"name": "lat", "in": "query", "required": True, "schema": {"type": "number"}},
                    {"name": "lon", "in": "query", "required": True, "schema": {"type": "number"}},
                ],
                "responses": {"200": {"description": "Distribuidores com ETA e estoque"}},
            }
        },
        "/api/comprador/cadastrar": {
            "post": {
                "summary": "Cadastro de dentista com validação de CRO",
                "responses": {"200": {"description": "Usuário cadastrado com status do CRO"}},
            }
        },
        "/api/checkout/pedido": {
            "post": {
                "summary": "Criação de pedido com trava sanitária e split",
                "responses": {"200": {"description": "Pedido pago com PIN gerado"}},
            }
        },
        "/api/telemetria/tracking": {
            "get": {
                "summary": "Live tracking da entrega com mapa e ETA",
                "parameters": [{"name": "pedido_id", "in": "query", "required": True, "schema": {"type": "string"}}],
                "responses": {"200": {"description": "Telemetria de entrega"}},
            }
        },
        "/api/telemetria/confirmar-pin": {
            "post": {
                "summary": "Confirmação de entrega segura com PIN de 4 dígitos",
                "responses": {"200": {"description": "Status de confirmação"}},
            }
        },
        "/api/radar/noticias": {
            "get": {
                "summary": "Clipping do Radar Odonto (Jornal Vivo)",
                "responses": {"200": {"description": "Notícias do mercado com fontes"}},
            }
        },
    },
}


class DentGoRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, data: Any):
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_html(self, status: int, html_str: str):
        payload = html_str.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _read_body_json(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        raw = self.rfile.read(content_length).decode("utf-8")
        return json.loads(raw)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_HEAD(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path in ["/", "/index.html", "/app"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
        else:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if path == "/api/saude":
            self._send_json(200, {"status": "operacional", "versao": "1.0.0", "engine": "sqlite-wal-python-puro"})
            return

        if path == "/api":
            html = f"""<!DOCTYPE html>
            <html>
            <head>
                <title>DentGo — Swagger Studio</title>
                <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
            </head>
            <body style="margin:0; background:#f8fafc;">
                <div id="swagger-ui"></div>
                <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
                <script>
                    SwaggerUIBundle({{
                        spec: {json.dumps(OPENAPI_SPEC)},
                        dom_id: '#swagger-ui',
                        deepLinking: true
                    }});
                </script>
            </body>
            </html>"""
            self._send_html(200, html)
            return

        if path == "/api/openapi.json":
            self._send_json(200, OPENAPI_SPEC)
            return

        if path == "/api/marcas":
            self._send_json(200, {"marcas": listar_marcas()})
            return

        if path == "/api/produtos":
            conexao = qs.get("conexao", [None])[0]
            marca_id = qs.get("marca_id", [None])[0]
            categoria = qs.get("categoria", [None])[0]
            diametro = float(qs["diametro"][0]) if "diametro" in qs else None

            produtos = buscar_produtos_cirurgicos(
                tipo_conexao=conexao,
                marca_id=marca_id,
                categoria=categoria,
                diametro=diametro,
            )
            self._send_json(200, {"total": len(produtos), "produtos": produtos})
            return

        if path == "/api/distribuidores/proximos":
            produto_id = qs.get("produto_id", [None])[0]
            lat = float(qs["lat"][0]) if "lat" in qs else None
            lon = float(qs["lon"][0]) if "lon" in qs else None

            if not produto_id or lat is None or lon is None:
                self._send_json(400, {"erro": "Parametros obrigatorios: produto_id, lat, lon"})
                return

            distribuidores = buscar_distribuidores_proximos_com_estoque(
                produto_id=produto_id,
                cliente_lat=lat,
                cliente_lon=lon,
            )
            self._send_json(200, {"total": len(distribuidores), "distribuidores": distribuidores})
            return

        if path == "/api/telemetria/tracking":
            pedido_id = qs.get("pedido_id", [None])[0]
            if not pedido_id:
                self._send_json(400, {"erro": "Parametro obrigatorio: pedido_id"})
                return
            try:
                dados = obter_telemetria_entrega(pedido_id)
                self._send_json(200, dados)
            except KeyError as e:
                self._send_json(404, {"erro": str(e)})
            return

        if path == "/api/radar/noticias":
            categoria = qs.get("categoria", [None])[0]
            marca = qs.get("marca", [None])[0]
            noticias = listar_radar_noticias(categoria=categoria, marca=marca)
            self._send_json(200, {"total": len(noticias), "noticias": noticias})
            return

        if path == "/manifest.json" or path.startswith("/manifest.json?"):
            caminho_manifest = pathlib.Path(__file__).resolve().parent.parent.parent / "desktop" / "manifest.json"
            if caminho_manifest.exists():
                data = caminho_manifest.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/manifest+json; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.end_headers()
                self.wfile.write(data)
                return

        if path == "/sw.js" or path.startswith("/sw.js?"):
            caminho_sw = pathlib.Path(__file__).resolve().parent.parent.parent / "desktop" / "sw.js"
            if caminho_sw.exists():
                data = caminho_sw.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/javascript; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.end_headers()
                self.wfile.write(data)
                return

        if path.startswith("/assets/"):
            clean_path = path.split("?")[0]
            caminho_asset = pathlib.Path(__file__).resolve().parent.parent.parent / "desktop" / clean_path.lstrip("/")
            if caminho_asset.exists() and caminho_asset.is_file():
                ext = caminho_asset.suffix.lower()
                mimes = {
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".svg": "image/svg+xml",
                    ".webp": "image/webp",
                    ".js": "application/javascript",
                    ".css": "text/css"
                }
                ctype = mimes.get(ext, "application/octet-stream")
                data = caminho_asset.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                if "/icons/" in path:
                    self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                else:
                    self.send_header("Cache-Control", "public, max-age=86400")
                self.end_headers()
                self.wfile.write(data)
                return

        if path == "/" or path == "/index.html" or path == "/app":
            caminho_app = pathlib.Path(__file__).resolve().parent.parent.parent / "desktop" / "index.html"
            if caminho_app.exists():
                conteudo = caminho_app.read_text(encoding="utf-8")
                self._send_html(200, conteudo)
                return

        if path == "/b2b" or path == "/b2b.html" or path == "/portal":
            caminho_b2b = pathlib.Path(__file__).resolve().parent.parent.parent / "desktop" / "b2b.html"
            if caminho_b2b.exists():
                conteudo = caminho_b2b.read_text(encoding="utf-8")
                self._send_html(200, conteudo)
                return

        if path == "/driver" or path == "/driver.html" or path == "/entregador":
            caminho_drv = pathlib.Path(__file__).resolve().parent.parent.parent / "desktop" / "driver.html"
            if caminho_drv.exists():
                conteudo = caminho_drv.read_text(encoding="utf-8")
                self._send_html(200, conteudo)
                return

        self._send_json(404, {"erro": "Rota nao encontrada"})

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._read_body_json()

        if path == "/api/comprador/cadastrar":
            try:
                user = cadastrar_comprador(
                    nome=body["nome"],
                    email=body["email"],
                    cpf=body["cpf"],
                    cro_numero=body["cro_numero"],
                    cro_uf=body["cro_uf"],
                    whatsapp=body["whatsapp"],
                )
                self._send_json(200, {"sucesso": True, "usuario": user})
            except Exception as e:
                self._send_json(400, {"erro": str(e)})
            return

        if path == "/api/checkout/pedido":
            try:
                pedido = criar_pedido(
                    comprador_id=body["comprador_id"],
                    distribuidor_id=body["distribuidor_id"],
                    itens=body["itens"],
                    modalidade_entrega=body.get("modalidade_entrega", "FLASH_2H"),
                    dest_latitude=float(body["dest_latitude"]),
                    dest_longitude=float(body["dest_longitude"]),
                    dest_endereco=body["dest_endereco"],
                    taxa_entrega=float(body.get("taxa_entrega", 18.0)),
                )
                self._send_json(200, {"sucesso": True, "pedido": pedido})
            except Exception as e:
                self._send_json(400, {"erro": str(e)})
            return

        if path == "/api/telemetria/confirmar-pin":
            try:
                ok = confirmar_entrega_com_pin(
                    pedido_id=body["pedido_id"],
                    pin_informado=body["pin"],
                )
                self._send_json(200, {"confirmado": ok, "status": "ENTREGUE" if ok else "PIN_INVALIDO"})
            except Exception as e:
                self._send_json(400, {"erro": str(e)})
            return

        self._send_json(404, {"erro": "Rota nao encontrada"})


def run_server(port: int = 8080):
    init_db()
    seed_marcas_canonicas()
    seed_noticias_iniciais()
    server_address = ("", port)
    httpd = HTTPServer(server_address, DentGoRequestHandler)
    print(f"[DentGo Server] Rodando deterministico em http://0.0.0.0:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()


if __name__ == "__main__":
    run_server()
