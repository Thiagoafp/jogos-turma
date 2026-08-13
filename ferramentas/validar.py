"""Valida as entregas em jogos/.

Roda automaticamente em cada pull request. Rode antes de abrir o seu:

    python ferramentas/validar.py

A ideia e que o aluno descubra o problema aqui, com uma mensagem em
portugues, e nao depois - com o site publicado quebrado.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA_ATIVIDADES = RAIZ / "atividades"

ENGINES = {"html", "construct", "pygame", "scratch"}
CAMPOS = ["titulo", "autor", "turma", "engine", "descricao", "controles"]
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
IMAGENS = {".png", ".jpg", ".jpeg", ".webp", ".svg"}

# avatar e banner do estudio: o quadrado do perfil e a arte de abertura
CAMPOS_ESTUDIO = {
    "avatar": "quadrada, pelo menos 128x128",
    "banner": "larga, algo como 1200x320",
}

LIMITE_ARQUIVO_MB = 25
LIMITE_PASTA_MB = 60


class Problemas:
    def __init__(self):
        self.erros: list[str] = []
        self.avisos: list[str] = []

    def erro(self, msg: str) -> None:
        self.erros.append(msg)

    def aviso(self, msg: str) -> None:
        self.avisos.append(msg)


def mb(caminho: Path) -> float:
    return caminho.stat().st_size / (1024 * 1024)


def validar_metadados(pasta: Path, p: Problemas) -> dict | None:
    arquivo = pasta / "jogo.json"
    if not arquivo.exists():
        p.erro("falta o arquivo jogo.json (copie de modelos/<engine>/jogo.json)")
        return None

    try:
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        p.erro("jogo.json precisa estar salvo em UTF-8")
        return None
    except json.JSONDecodeError as e:
        p.erro(f"jogo.json com erro de sintaxe na linha {e.lineno}: {e.msg}")
        return None

    if not isinstance(dados, dict):
        p.erro("jogo.json deve conter um objeto { ... }")
        return None

    for campo in CAMPOS:
        valor = dados.get(campo)
        if not isinstance(valor, str) or not valor.strip():
            p.erro(f'jogo.json: falta o campo "{campo}" (ou esta vazio)')

    engine = dados.get("engine")
    if engine and engine not in ENGINES:
        p.erro(
            f'jogo.json: engine "{engine}" nao existe. '
            f"Use uma destas: {', '.join(sorted(ENGINES))}"
        )

    if len(str(dados.get("descricao", ""))) > 300:
        p.aviso("a descricao esta longa; o card da galeria corta em ~300 caracteres")

    capa = dados.get("capa")
    if capa:
        arq_capa = pasta / capa
        if not arq_capa.exists():
            p.erro(f'jogo.json aponta a capa "{capa}", mas o arquivo nao esta na pasta')
        elif arq_capa.suffix.lower() not in IMAGENS:
            p.erro(f"a capa precisa ser {', '.join(sorted(IMAGENS))}")

    return dados


def _chamada_de(no: ast.AST, modulo: str, funcao: str) -> bool:
    """True se `no` for uma chamada modulo.funcao(...) - ex: asyncio.sleep(0)."""
    return (
        isinstance(no, ast.Call)
        and isinstance(no.func, ast.Attribute)
        and no.func.attr == funcao
        and isinstance(no.func.value, ast.Name)
        and no.func.value.id == modulo
    )


def validar_pygame(principal: Path, p: Problemas) -> None:
    """Confere as regras do pygbag lendo a ARVORE do codigo, nao o texto.

    Procurar por texto ("asyncio.run(" in codigo) reprova quem apenas cita a
    regra num comentario - foi o que aconteceu com o proprio modelo.
    """
    if not principal.exists():
        p.erro("falta main.py na raiz da sua pasta (o nome precisa ser esse)")
        return

    codigo = principal.read_text(encoding="utf-8", errors="ignore")
    try:
        arvore = ast.parse(codigo)
    except SyntaxError as e:
        p.erro(f"main.py tem erro de sintaxe na linha {e.lineno}: {e.msg}")
        return

    nos = list(ast.walk(arvore))

    if not any(_chamada_de(n, "asyncio", "run") for n in nos):
        p.erro(
            "main.py nao chama asyncio.run(main()). Sem isso o jogo nao roda "
            "no navegador - veja a REGRA 2 em modelos/pygame/main.py"
        )

    if not any(
        isinstance(n, ast.Await) and _chamada_de(n.value, "asyncio", "sleep")
        for n in nos
    ):
        p.erro(
            "falta 'await asyncio.sleep(0)' no fim do loop principal. Sem essa "
            "linha a aba do navegador congela - veja a REGRA 3 em "
            "modelos/pygame/main.py"
        )

    for no in nos:
        if isinstance(no, ast.Call) and isinstance(no.func, ast.Name):
            if no.func.id == "input":
                p.erro(
                    f"input() na linha {no.lineno} nao funciona no navegador; "
                    "use eventos do pygame"
                )
            elif no.func.id == "open":
                p.aviso(
                    f"open() na linha {no.lineno}: ler arquivo da sua pasta "
                    "funciona, escrever nao"
                )
        elif isinstance(no, (ast.Import, ast.ImportFrom)):
            nome = getattr(no, "module", "") or ""
            nomes = [a.name for a in no.names] + [nome]
            if any(n.split(".")[0] == "threading" for n in nomes if n):
                p.aviso("threading nao funciona no navegador")


def validar_conteudo(pasta: Path, dados: dict, p: Problemas) -> None:
    engine = dados.get("engine")

    if engine in ("html", "construct"):
        indice = pasta / "index.html"
        if not indice.exists():
            p.erro(
                "falta index.html na raiz da sua pasta. "
                + (
                    "No Construct: Menu > Export > Web (HTML5) e commite TODO o "
                    "conteudo da pasta exportada."
                    if engine == "construct"
                    else "O arquivo principal precisa se chamar index.html."
                )
            )
        else:
            texto = indice.read_text(encoding="utf-8", errors="ignore")
            if re.search(r'(src|href)\s*=\s*[\'"]/(?!/)', texto):
                p.erro(
                    "index.html usa caminho absoluto (src=\"/algo\"). "
                    "No site publicado isso quebra: use caminho relativo "
                    '(src="algo" ou src="./algo").'
                )
            if re.search(r'(src|href)\s*=\s*[\'"]https?://', texto):
                p.aviso(
                    "index.html carrega arquivo de outro site (CDN). Se o site "
                    "sair do ar, o jogo para: baixe o arquivo e commite junto."
                )

    elif engine == "pygame":
        validar_pygame(pasta / "main.py", p)

    elif engine == "scratch":
        tem_id = str(dados.get("scratch_id", "")).strip().isdigit()
        tem_html = (pasta / "index.html").exists()
        if not tem_id and not tem_html:
            p.erro(
                "para Scratch, escolha um dos dois: (a) publique o projeto no "
                'scratch.mit.edu e coloque "scratch_id": "123456789" no '
                "jogo.json (o numero que aparece no fim do link do projeto), ou "
                "(b) exporte pelo TurboWarp Packager e commite o index.html."
            )


def validar_tamanho(pasta: Path, p: Problemas) -> None:
    total = 0.0
    for arquivo in pasta.rglob("*"):
        if not arquivo.is_file():
            continue
        tamanho = mb(arquivo)
        total += tamanho
        if tamanho > LIMITE_ARQUIVO_MB:
            p.erro(
                f"{arquivo.relative_to(pasta)} tem {tamanho:.1f} MB "
                f"(limite {LIMITE_ARQUIVO_MB} MB por arquivo)"
            )
    if total > LIMITE_PASTA_MB:
        p.erro(
            f"a pasta inteira tem {total:.1f} MB "
            f"(limite {LIMITE_PASTA_MB} MB). Comprima imagens e sons."
        )


def validar_jogo(pasta: Path) -> Problemas:
    p = Problemas()

    if not SLUG.match(pasta.name):
        p.erro(
            f'"{pasta.name}" nao serve como nome de pasta. Use so letras '
            "minusculas, numeros e hifen - por exemplo: maria-silva-corrida"
        )

    dados = validar_metadados(pasta, p)
    if dados:
        validar_conteudo(pasta, dados, p)
    validar_tamanho(pasta, p)
    return p


def validar_estudio(dir_aluno: Path) -> Problemas:
    """Confere o aluno.json: identidade do estudio, avatar e banner.

    Tudo aqui e opcional - quem nao configurar nada ganha uma capa gerada
    com as iniciais. So reclamamos do que esta declarado e errado.
    """
    p = Problemas()
    arquivo = dir_aluno / "aluno.json"

    if not arquivo.exists():
        p.aviso(
            "sem aluno.json: o estudio vai aparecer com o nome da pasta e uma "
            "capa gerada. Copie de modelos/aluno.json para personalizar."
        )
        return p

    try:
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        p.erro("aluno.json precisa estar salvo em UTF-8")
        return p
    except json.JSONDecodeError as e:
        p.erro(f"aluno.json com erro de sintaxe na linha {e.lineno}: {e.msg}")
        return p

    if not str(dados.get("nome", "")).strip():
        p.erro('aluno.json: falta o campo "nome"')

    if len(str(dados.get("lema", ""))) > 160:
        p.aviso("o lema esta longo; o ideal e caber numa linha (ate 160 letras)")

    cor = str(dados.get("cor", "")).strip()
    if cor and not re.fullmatch(r"#[0-9a-fA-F]{6}", cor):
        p.erro(f'aluno.json: cor "{cor}" invalida. Use o formato #RRGGBB, '
               "por exemplo #7f5af0")

    for campo, formato in CAMPOS_ESTUDIO.items():
        nome = str(dados.get(campo, "")).strip()
        if not nome:
            continue
        imagem = dir_aluno / nome
        if not imagem.exists():
            p.erro(f'aluno.json aponta o {campo} "{nome}", mas o arquivo nao '
                   "esta na sua pasta")
        elif imagem.suffix.lower() not in IMAGENS:
            p.erro(f"o {campo} precisa ser {', '.join(sorted(IMAGENS))}")
        elif mb(imagem) > 4:
            p.erro(f"o {campo} tem {mb(imagem):.1f} MB; comprima para menos de "
                   f"4 MB (imagem {formato})")

    return p


def localizar_jogos() -> list[Path]:
    """atividades/<curso>/<escola>/alunos/<aluno>/<jogo>/"""
    encontrados = []
    if not PASTA_ATIVIDADES.exists():
        return encontrados
    for curso in sorted(d for d in PASTA_ATIVIDADES.iterdir() if d.is_dir()):
        for escola in sorted(d for d in curso.iterdir() if d.is_dir()):
            alunos = escola / "alunos"
            if not alunos.is_dir():
                continue
            for aluno in sorted(d for d in alunos.iterdir() if d.is_dir()):
                for jogo in sorted(d for d in aluno.iterdir() if d.is_dir()):
                    encontrados.append(jogo)
    return encontrados


def main() -> int:
    if not PASTA_ATIVIDADES.exists():
        print(f"pasta {PASTA_ATIVIDADES} nao existe")
        return 1

    pastas = localizar_jogos()
    if not pastas:
        print("nenhum jogo entregue ainda - nada a validar")
        return 0

    total_erros = 0

    for dir_aluno in sorted({p.parent for p in pastas}):
        p = validar_estudio(dir_aluno)
        total_erros += len(p.erros)
        if p.erros or p.avisos:
            print(f"\n[estudio] {dir_aluno.name}")
            for e in p.erros:
                print(f"     ERRO: {e}")
            for a in p.avisos:
                print(f"     aviso: {a}")

    for pasta in pastas:
        p = validar_jogo(pasta)
        total_erros += len(p.erros)
        rotulo = f"{pasta.parent.name}/{pasta.name}"

        if p.erros:
            print(f"\n[X] {rotulo}")
        elif p.avisos:
            print(f"\n[!] {rotulo}")
        else:
            print(f"[ok] {rotulo}")

        for e in p.erros:
            print(f"     ERRO: {e}")
        for a in p.avisos:
            print(f"     aviso: {a}")

    print(f"\n{len(pastas)} jogo(s) verificado(s), {total_erros} erro(s).")
    return 1 if total_erros else 0


if __name__ == "__main__":
    sys.exit(main())
