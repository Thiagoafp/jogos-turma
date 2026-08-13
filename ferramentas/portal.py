"""Portal local para alunos criarem estudios e enviarem jogos."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import mimetypes
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
import zipfile
from email.parser import BytesParser
from email.policy import default
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath

from validar import LIMITE_ARQUIVO_MB, LIMITE_PASTA_MB, SLUG, validar_estudio, validar_jogo

RAIZ = Path(__file__).resolve().parent.parent
PORTAL_WEB = RAIZ / "portal"
PASTA_LOCAL = RAIZ / ".portal"
ACESSOS = PASTA_LOCAL / "acessos.json"
CODIGOS_INICIAIS = PASTA_LOCAL / "codigos-iniciais.txt"
MAX_REQUISICAO = 65 * 1024 * 1024
MAX_IMAGEM = 4 * 1024 * 1024
IMAGENS_SEGURAS = {".png", ".jpg", ".jpeg", ".webp"}
ENGINES = {"html", "construct", "pygame", "scratch", "link"}
SESSOES: dict[str, tuple[str, float]] = {}
TRAVA_BUILD = threading.Lock()


def ler_json(caminho: Path) -> dict:
    return json.loads(caminho.read_text(encoding="utf-8"))


def gravar_json(caminho: Path, dados: dict) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(caminho.suffix + ".tmp")
    temporario.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporario.replace(caminho)


def hash_codigo(codigo: str, sal_hex: str | None = None) -> dict[str, str]:
    sal = bytes.fromhex(sal_hex) if sal_hex else secrets.token_bytes(16)
    resumo = hashlib.pbkdf2_hmac("sha256", codigo.encode(), sal, 180_000)
    return {"sal": sal.hex(), "hash": resumo.hex()}


def conferir_codigo(codigo: str, registro: dict) -> bool:
    calculado = hash_codigo(codigo, registro["sal"])["hash"]
    return hmac.compare_digest(calculado, registro["hash"])


def localizar_alunos(curso: str | None, escola: str | None) -> tuple[Path, list[dict]]:
    bases = []
    for curso_dir in sorted((RAIZ / "atividades").glob("*")):
        if not curso_dir.is_dir() or (curso and curso_dir.name != curso):
            continue
        for escola_dir in sorted(curso_dir.glob("*")):
            alunos_dir = escola_dir / "alunos"
            if alunos_dir.is_dir() and (not escola or escola_dir.name == escola):
                bases.append(alunos_dir)
    if len(bases) != 1:
        nomes = ", ".join(str(p.relative_to(RAIZ)) for p in bases) or "nenhuma"
        raise RuntimeError("Informe --curso e --escola; era esperada uma turma, encontrei: " + nomes)
    base = bases[0]
    alunos = []
    for pasta in sorted(p for p in base.iterdir() if p.is_dir() and p.name != "professor"):
        ficha = pasta / "aluno.json"
        dados = ler_json(ficha) if ficha.exists() else {}
        alunos.append({"slug": pasta.name, "pasta": pasta, "dados": dados})
    return base, alunos


def garantir_acessos(alunos: list[dict], redefinir: bool = False) -> list[tuple[str, str, str]]:
    PASTA_LOCAL.mkdir(exist_ok=True)
    dados = ler_json(ACESSOS) if ACESSOS.exists() else {"alunos": {}}
    criados = []
    for aluno in alunos:
        slug = aluno["slug"]
        if slug in dados["alunos"] and not redefinir:
            continue
        codigo = "-".join((secrets.token_hex(2), secrets.token_hex(2))).upper()
        dados["alunos"][slug] = hash_codigo(codigo)
        criados.append((slug, aluno["dados"].get("nome", slug), codigo))
    gravar_json(ACESSOS, dados)
    if criados:
        linhas = ["CÓDIGOS DO PORTAL — entregue cada linha somente ao respectivo aluno", ""]
        linhas.extend(f"{nome} ({slug}): {codigo}" for slug, nome, codigo in criados)
        CODIGOS_INICIAIS.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return criados


def campos_multipart(tipo: str, corpo: bytes) -> tuple[dict[str, str], dict[str, tuple[str, bytes]]]:
    cabecalho = b"Content-Type: " + tipo.encode("ascii") + b"\r\nMIME-Version: 1.0\r\n\r\n"
    mensagem = BytesParser(policy=default).parsebytes(cabecalho + corpo)
    if not mensagem.is_multipart():
        raise ValueError("Formulário de envio inválido.")
    campos, arquivos = {}, {}
    for parte in mensagem.iter_parts():
        nome = parte.get_param("name", header="content-disposition")
        if not nome:
            continue
        conteudo = parte.get_payload(decode=True) or b""
        arquivo = parte.get_filename()
        if arquivo:
            arquivos[nome] = (Path(arquivo).name, conteudo)
        else:
            campos[nome] = conteudo.decode(parte.get_content_charset() or "utf-8", errors="replace")
    return campos, arquivos


def extrair_zip_seguro(conteudo: bytes, destino: Path) -> None:
    arquivo_zip = destino.parent / "envio.zip"
    arquivo_zip.write_bytes(conteudo)
    total = 0
    try:
        with zipfile.ZipFile(arquivo_zip) as z:
            membros = [m for m in z.infolist() if not m.is_dir()]
            if not membros:
                raise ValueError("O ZIP está vazio.")
            for membro in membros:
                partes = PurePosixPath(membro.filename.replace("\\", "/")).parts
                if (PurePosixPath(membro.filename.replace("\\", "/")).is_absolute()
                        or not partes or any(p in {"", ".", ".."} for p in partes)
                        or partes[0].endswith(":")):
                    raise ValueError(f"Caminho inseguro dentro do ZIP: {membro.filename}")
                if membro.file_size > LIMITE_ARQUIVO_MB * 1024 * 1024:
                    raise ValueError(f"{membro.filename} excede {LIMITE_ARQUIVO_MB} MB.")
                total += membro.file_size
            if total > LIMITE_PASTA_MB * 1024 * 1024:
                raise ValueError(f"O conteúdo do ZIP excede {LIMITE_PASTA_MB} MB.")
            z.extractall(destino)
    except zipfile.BadZipFile as exc:
        raise ValueError("O arquivo enviado não é um ZIP válido.") from exc
    finally:
        arquivo_zip.unlink(missing_ok=True)
    itens = list(destino.iterdir())
    if len(itens) == 1 and itens[0].is_dir():
        interna = itens[0]
        for item in list(interna.iterdir()):
            shutil.move(str(item), destino / item.name)
        interna.rmdir()


def executar_build() -> tuple[bool, str]:
    with TRAVA_BUILD:
        processo = subprocess.run(
            [sys.executable, str(RAIZ / "ferramentas" / "construir.py")], cwd=RAIZ,
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240,
        )
    saida = (processo.stdout + "\n" + processo.stderr).strip()
    return processo.returncode == 0, saida[-4000:]


class Portal:
    def __init__(self, base: Path, alunos: list[dict]):
        self.base = base
        self.alunos = {a["slug"]: a for a in alunos}
        self.acessos = ler_json(ACESSOS)["alunos"]

    def publico(self) -> list[dict]:
        return [{"slug": slug, "nome": a["dados"].get("nome", slug)} for slug, a in sorted(
            self.alunos.items(), key=lambda item: item[1]["dados"].get("nome", item[0]))]

    def autenticar(self, slug: str, codigo: str) -> str | None:
        registro = self.acessos.get(slug)
        if not registro or not conferir_codigo(codigo.strip().upper(), registro):
            return None
        token = secrets.token_urlsafe(32)
        SESSOES[token] = (slug, time.time() + 8 * 3600)
        return token

    def aluno_da_sessao(self, token: str | None) -> dict | None:
        if not token or token not in SESSOES:
            return None
        slug, expira = SESSOES[token]
        if expira < time.time():
            SESSOES.pop(token, None)
            return None
        return self.alunos.get(slug)


class Handler(BaseHTTPRequestHandler):
    server_version = "PortalJogos/1.0"

    @property
    def app(self) -> Portal:
        return self.server.app  # type: ignore[attr-defined]

    def enviar_json(self, dados, status: int = 200, cookie: str | None = None) -> None:
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(corpo)

    def erro(self, mensagem: str, status: int = 400) -> None:
        self.enviar_json({"ok": False, "erro": mensagem}, status)

    def token(self) -> str | None:
        cookies = SimpleCookie(self.headers.get("Cookie", ""))
        return cookies["portal_sessao"].value if "portal_sessao" in cookies else None

    def aluno(self) -> dict | None:
        aluno = self.app.aluno_da_sessao(self.token())
        if not aluno:
            self.erro("Sessão expirada. Entre novamente.", HTTPStatus.UNAUTHORIZED)
        return aluno

    def ler_corpo(self) -> bytes | None:
        try:
            tamanho = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.erro("Tamanho da requisição inválido.")
            return None
        if tamanho <= 0 or tamanho > MAX_REQUISICAO:
            self.erro("Envio vazio ou maior que 65 MB.", HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
            return None
        return self.rfile.read(tamanho)

    def do_GET(self) -> None:
        caminho = urllib.parse.urlparse(self.path).path
        if caminho == "/api/alunos":
            return self.enviar_json(self.app.publico())
        if caminho == "/api/me":
            aluno = self.aluno()
            if not aluno:
                return
            dados = ler_json(aluno["pasta"] / "aluno.json")
            jogos = []
            for pasta in sorted(p for p in aluno["pasta"].iterdir() if p.is_dir()):
                ficha = pasta / "jogo.json"
                if ficha.exists():
                    item = ler_json(ficha)
                    jogos.append({"slug": pasta.name, "titulo": item.get("titulo", pasta.name), "engine": item.get("engine", "")})
            return self.enviar_json({"aluno": aluno["slug"], "estudio": dados, "jogos": jogos})
        if caminho == "/":
            caminho = "/index.html"
        arquivo = (PORTAL_WEB / caminho.lstrip("/")).resolve()
        try:
            arquivo.relative_to(PORTAL_WEB.resolve())
        except ValueError:
            return self.send_error(404)
        if not arquivo.is_file():
            return self.send_error(404)
        conteudo = arquivo.read_bytes()
        self.send_response(200)
        tipo = mimetypes.guess_type(arquivo.name)[0] or "application/octet-stream"
        self.send_header("Content-Type", tipo + ("; charset=utf-8" if arquivo.suffix in {".html", ".css", ".js"} else ""))
        self.send_header("Content-Length", str(len(conteudo)))
        self.end_headers()
        self.wfile.write(conteudo)

    def do_POST(self) -> None:
        caminho = urllib.parse.urlparse(self.path).path
        corpo = self.ler_corpo()
        if corpo is None:
            return
        try:
            if caminho == "/api/entrar":
                dados = json.loads(corpo)
                token = self.app.autenticar(str(dados.get("aluno", "")), str(dados.get("codigo", "")))
                if not token:
                    return self.erro("Aluno ou código incorreto.", HTTPStatus.UNAUTHORIZED)
                cookie = f"portal_sessao={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800"
                return self.enviar_json({"ok": True}, cookie=cookie)
            if caminho == "/api/sair":
                SESSOES.pop(self.token() or "", None)
                return self.enviar_json({"ok": True}, cookie="portal_sessao=; Path=/; Max-Age=0; SameSite=Strict")
            if caminho == "/api/estudio":
                return self.salvar_estudio(corpo)
            if caminho == "/api/jogos":
                return self.salvar_jogo(corpo)
            self.erro("Rota não encontrada.", 404)
        except (ValueError, json.JSONDecodeError) as exc:
            self.erro(str(exc))
        except subprocess.TimeoutExpired:
            self.erro("A construção da galeria excedeu quatro minutos.", 504)
        except Exception as exc:
            print(f"ERRO {caminho}: {exc!r}", file=sys.stderr)
            self.erro("Não foi possível concluir o envio. Consulte o professor.", 500)

    def salvar_estudio(self, corpo: bytes) -> None:
        aluno = self.aluno()
        if not aluno:
            return
        campos, arquivos = campos_multipart(self.headers.get("Content-Type", ""), corpo)
        nome, lema, cor = campos.get("estudio", "").strip(), campos.get("lema", "").strip(), campos.get("cor", "").strip()
        if not nome or len(nome) > 60:
            raise ValueError("O nome do estúdio deve ter de 1 a 60 caracteres.")
        if len(lema) > 160:
            raise ValueError("O lema deve ter no máximo 160 caracteres.")
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", cor):
            raise ValueError("Escolha uma cor válida.")
        pasta, ficha = aluno["pasta"], aluno["pasta"] / "aluno.json"
        anterior, dados, backups = ficha.read_bytes(), ler_json(ficha), {}
        dados.update({"estudio": nome, "lema": lema, "cor": cor})
        for campo in ("avatar", "banner"):
            if campo not in arquivos or not arquivos[campo][1]:
                continue
            nome_original, conteudo = arquivos[campo]
            extensao = Path(nome_original).suffix.lower()
            if extensao not in IMAGENS_SEGURAS or len(conteudo) > MAX_IMAGEM:
                raise ValueError(f"{campo}: use PNG, JPG ou WEBP com até 4 MB.")
        for campo in ("avatar", "banner"):
            if campo not in arquivos or not arquivos[campo][1]:
                continue
            nome_original, conteudo = arquivos[campo]
            extensao = Path(nome_original).suffix.lower()
            destino = pasta / f"{campo}{extensao}"
            backups[destino] = destino.read_bytes() if destino.exists() else None
            destino.write_bytes(conteudo)
            dados[campo] = destino.name
        gravar_json(ficha, dados)
        problemas = validar_estudio(pasta)
        if problemas.erros:
            ficha.write_bytes(anterior)
            self._restaurar(backups)
            raise ValueError(" ".join(problemas.erros))
        ok, saida = executar_build()
        if not ok:
            ficha.write_bytes(anterior)
            self._restaurar(backups)
            raise ValueError("A galeria não pôde ser reconstruída. " + saida[-800:])
        aluno["dados"] = dados
        self.enviar_json({"ok": True, "mensagem": "Estúdio salvo e galeria atualizada."})

    @staticmethod
    def _restaurar(backups: dict[Path, bytes | None]) -> None:
        for arquivo, conteudo in backups.items():
            arquivo.write_bytes(conteudo) if conteudo is not None else arquivo.unlink(missing_ok=True)

    def salvar_jogo(self, corpo: bytes) -> None:
        aluno = self.aluno()
        if not aluno:
            return
        campos, arquivos = campos_multipart(self.headers.get("Content-Type", ""), corpo)
        slug, engine, titulo = campos.get("slug", "").strip().lower(), campos.get("engine", "").strip(), campos.get("titulo", "").strip()
        if not SLUG.fullmatch(slug):
            raise ValueError("O endereço deve usar letras minúsculas, números e hífen.")
        if engine not in ENGINES:
            raise ValueError("Tipo de jogo inválido.")
        if not titulo or len(titulo) > 80:
            raise ValueError("O título deve ter de 1 a 80 caracteres.")
        destino = aluno["pasta"] / slug
        if destino.exists() and campos.get("substituir") != "sim":
            raise ValueError("Já existe um jogo com esse endereço. Marque a opção para substituí-lo.")
        with tempfile.TemporaryDirectory(dir=PASTA_LOCAL) as tmp:
            estagio = Path(tmp) / slug
            estagio.mkdir()
            precisa_zip = engine in {"html", "construct", "pygame"} or (engine == "scratch" and arquivos.get("pacote", ("", b""))[1])
            if precisa_zip:
                pacote = arquivos.get("pacote")
                if not pacote or not pacote[1]:
                    raise ValueError("Envie o pacote ZIP do jogo.")
                if Path(pacote[0]).suffix.lower() != ".zip":
                    raise ValueError("O pacote do jogo precisa ser um arquivo .zip.")
                extrair_zip_seguro(pacote[1], estagio)
            dados = {
                "titulo": titulo, "autor": aluno["dados"].get("nome", aluno["slug"]),
                "turma": aluno["dados"].get("turma", "") or "Técnico em Programação de Jogos Digitais",
                "engine": engine, "descricao": campos.get("descricao", "").strip(),
                "controles": campos.get("controles", "").strip() or "Veja as instruções no jogo.",
            }
            if engine == "scratch" and campos.get("scratch_id", "").strip():
                dados["scratch_id"] = campos["scratch_id"].strip()
            if engine == "link":
                dados["url"] = campos.get("url", "").strip()
            capa = arquivos.get("capa")
            if capa and capa[1]:
                ext = Path(capa[0]).suffix.lower()
                if ext not in IMAGENS_SEGURAS or len(capa[1]) > MAX_IMAGEM:
                    raise ValueError("Capa: use PNG, JPG ou WEBP com até 4 MB.")
                dados["capa"] = "capa" + ext
                (estagio / dados["capa"]).write_bytes(capa[1])
            gravar_json(estagio / "jogo.json", dados)
            problemas = validar_jogo(estagio)
            if problemas.erros:
                raise ValueError("Corrija o jogo: " + " ".join(problemas.erros))
            backup = None
            if destino.exists():
                backup = Path(tmp) / "backup"
                shutil.move(destino, backup)
            shutil.move(estagio, destino)
            ok, saida = executar_build()
            if not ok:
                shutil.rmtree(destino, ignore_errors=True)
                if backup:
                    shutil.move(backup, destino)
                raise ValueError("O jogo passou pela validação, mas a galeria falhou: " + saida[-800:])
        self.enviar_json({"ok": True, "mensagem": "Jogo enviado, validado e publicado na galeria."})


def main() -> int:
    parser = argparse.ArgumentParser(description="portal local de envio dos jogos")
    parser.add_argument("--porta", type=int, default=8081)
    parser.add_argument("--host", default="127.0.0.1", help="use 0.0.0.0 para acesso na rede da escola")
    parser.add_argument("--curso")
    parser.add_argument("--escola")
    parser.add_argument("--redefinir-codigos", action="store_true", help="gera e mostra novos códigos para todos")
    args = parser.parse_args()
    base, alunos = localizar_alunos(args.curso, args.escola)
    criados = garantir_acessos(alunos, redefinir=args.redefinir_codigos)
    if criados:
        print("\nCódigos criados (entregue cada código somente ao respectivo aluno):")
        for slug, nome, codigo in criados:
            print(f"  {nome:<24} {slug:<16} {codigo}")
        print(f"\nLista para o professor: {CODIGOS_INICIAIS}")
        print("Os códigos ficam armazenados como hash e não entram no Git.")
    servidor = ThreadingHTTPServer((args.host, args.porta), Handler)
    servidor.app = Portal(base, alunos)  # type: ignore[attr-defined]
    print(f"\nPortal da turma em http://localhost:{args.porta}")
    print("A galeria continua em http://localhost:8080  (Ctrl+C para parar)")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nPortal encerrado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
