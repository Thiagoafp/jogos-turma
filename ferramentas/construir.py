"""Monta o site estatico em site/ a partir das entregas em jogos/.

    python ferramentas/construir.py            # tudo
    python ferramentas/construir.py --sem-pygame   # pula a compilacao WASM
    python ferramentas/construir.py --servir       # constroi e abre um servidor

Cada engine chega ao mesmo formato final - uma pasta com index.html:

    html / construct  a pasta do aluno ja e isso: so copiar
    pygame            compilado para WebAssembly com pygbag
    scratch           pagina gerada com o player do scratch.mit.edu

Resultado:

    site/index.html          galeria (a pagina que os pais abrem)
    site/j/<slug>.html       pagina de cada jogo: titulo, autor, controles
    site/jogos/<slug>/       o jogo em si, dentro de um iframe
"""

from __future__ import annotations

import argparse
import html
import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA_JOGOS = RAIZ / "jogos"
SAIDA = RAIZ / "site"

TITULO_SITE = "Jogos da Turma"
SUBTITULO = "Projetos criados pelos alunos - clique para jogar no navegador"

CORES_ENGINE = {
    "pygame": ("#3776ab", "Python / pygame"),
    "construct": ("#00c8a0", "Construct"),
    "scratch": ("#f59a23", "Scratch"),
    "html": ("#e34f26", "HTML / JavaScript"),
}

# paleta para a capa gerada quando o aluno nao manda imagem
GRADIENTES = [
    ("#7f5af0", "#2cb67d"), ("#ff8906", "#f25f4c"), ("#2cb67d", "#0f80aa"),
    ("#e53170", "#7f5af0"), ("#f9bc60", "#e16162"), ("#00b4d8", "#0077b6"),
    ("#8338ec", "#3a86ff"), ("#fb5607", "#ffbe0b"), ("#06d6a0", "#118ab2"),
    ("#ef476f", "#ffd166"),
]


def esc(texto: object) -> str:
    return html.escape(str(texto), quote=True)


# ---------------------------------------------------------------- leitura


def carregar_jogos() -> list[dict]:
    jogos = []
    if not PASTA_JOGOS.exists():
        return jogos

    for pasta in sorted(d for d in PASTA_JOGOS.iterdir() if d.is_dir()):
        arquivo = pasta / "jogo.json"
        if not arquivo.exists():
            print(f"  ! {pasta.name}: sem jogo.json, ignorando")
            continue
        try:
            dados = json.loads(arquivo.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"  ! {pasta.name}: jogo.json invalido ({e}), ignorando")
            continue
        dados["slug"] = pasta.name
        dados["pasta"] = pasta
        jogos.append(dados)

    jogos.sort(key=lambda j: str(j.get("titulo", "")).lower())
    return jogos


# ---------------------------------------------------------------- engines


def copiar_pasta_web(jogo: dict, destino: Path) -> bool:
    """html e construct: a entrega ja e um site."""
    if not (jogo["pasta"] / "index.html").exists():
        print(f"  ! {jogo['slug']}: sem index.html, pulando")
        return False
    shutil.copytree(
        jogo["pasta"],
        destino,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("jogo.json", "*.py", "__pycache__", ".*"),
    )
    return True


def compilar_pygame(jogo: dict, destino: Path) -> bool:
    """pygbag compila main.py para WebAssembly."""
    pasta = jogo["pasta"]
    if not (pasta / "main.py").exists():
        print(f"  ! {jogo['slug']}: sem main.py, pulando")
        return False

    construido = pasta / "build" / "web"
    if construido.exists():
        shutil.rmtree(construido)

    comando = [
        sys.executable, "-m", "pygbag",
        "--build",              # so compila, nao abre servidor
        "--ume_block", "0",     # nao exige clique antes de iniciar
        str(pasta),
    ]
    print(f"    compilando com pygbag (pode demorar)...")
    resultado = subprocess.run(comando, capture_output=True, text=True)

    if not construido.exists():
        print(f"  ! {jogo['slug']}: pygbag falhou")
        saida = (resultado.stdout + resultado.stderr).strip().splitlines()
        for linha in saida[-15:]:
            print(f"      {linha}")
        return False

    shutil.copytree(construido, destino, dirs_exist_ok=True)
    return True


def pagina_scratch(jogo: dict, destino: Path) -> bool:
    """Scratch publicado: usa o player oficial dentro de um iframe."""
    if (jogo["pasta"] / "index.html").exists():
        # exportado pelo TurboWarp Packager: e um site normal
        return copiar_pasta_web(jogo, destino)

    projeto = str(jogo.get("scratch_id", "")).strip()
    if not projeto.isdigit():
        print(f"  ! {jogo['slug']}: sem scratch_id nem index.html, pulando")
        return False

    destino.mkdir(parents=True, exist_ok=True)
    (destino / "index.html").write_text(
        f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(jogo.get('titulo', ''))}</title>
  <style>
    html,body {{ margin:0; height:100%; background:#12162d;
                 display:grid; place-items:center; }}
    iframe {{ border:0; width:485px; height:402px; max-width:100%; }}
  </style>
</head>
<body>
  <iframe src="https://scratch.mit.edu/projects/{esc(projeto)}/embed"
          allowtransparency="true" allowfullscreen
          title="{esc(jogo.get('titulo', ''))}"></iframe>
</body>
</html>
""",
        encoding="utf-8",
    )
    return True


CONSTRUTORES = {
    "html": copiar_pasta_web,
    "construct": copiar_pasta_web,
    "pygame": compilar_pygame,
    "scratch": pagina_scratch,
}


# ---------------------------------------------------------------- paginas

ESTILO = """
:root {
  --fundo: #0d1020; --carta: #171b33; --borda: #262c4d;
  --texto: #eef0ff; --suave: #a3a9cc; --destaque: #ffd23c;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--fundo); color: var(--texto);
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  line-height: 1.5;
}
a { color: inherit; text-decoration: none; }
.envolucro { max-width: 1200px; margin: 0 auto; padding: 2rem 1.25rem 4rem; }

header.topo { text-align: center; padding: 3rem 1rem 2.5rem; }
header.topo h1 {
  margin: 0; font-size: clamp(2rem, 6vw, 3.2rem); letter-spacing: -.02em;
}
header.topo p { margin: .6rem 0 0; color: var(--suave); }

.grade {
  display: grid; gap: 1.4rem;
  grid-template-columns: repeat(auto-fill, minmax(270px, 1fr));
}

.carta {
  background: var(--carta); border: 1px solid var(--borda);
  border-radius: 14px; overflow: hidden;
  display: flex; flex-direction: column;
  transition: transform .15s ease, border-color .15s ease;
}
.carta:hover { transform: translateY(-4px); border-color: var(--destaque); }
.carta .capa {
  aspect-ratio: 16/10; display: grid; place-items: center;
  font-size: 2.6rem; font-weight: 700; color: #fff;
  text-shadow: 0 2px 12px rgba(0,0,0,.35);
}
.carta .capa img { width: 100%; height: 100%; object-fit: cover; display: block; }
.carta .corpo { padding: 1rem 1.1rem 1.2rem; flex: 1; display: flex;
                flex-direction: column; gap: .45rem; }
.carta h2 { margin: 0; font-size: 1.15rem; }
.carta .autor { color: var(--suave); font-size: .92rem; }
.carta .desc { color: var(--suave); font-size: .88rem; flex: 1; }
.etiqueta {
  align-self: flex-start; font-size: .72rem; font-weight: 600;
  padding: .18rem .6rem; border-radius: 999px; color: #06121f;
}
.jogar {
  margin-top: .4rem; text-align: center; font-weight: 600;
  background: var(--destaque); color: #14161f;
  padding: .55rem; border-radius: 9px;
}

/* pagina de um jogo */
.barra {
  display: flex; align-items: center; gap: 1rem; flex-wrap: wrap;
  padding: .9rem 1.25rem; background: var(--carta);
  border-bottom: 1px solid var(--borda);
}
.barra h1 { margin: 0; font-size: 1.15rem; }
.barra .autor { color: var(--suave); font-size: .9rem; }
.barra .voltar { margin-left: auto; color: var(--suave); font-size: .92rem; }
.barra .voltar:hover { color: var(--destaque); }
.palco { padding: 1.25rem; display: grid; place-items: center; }
.palco iframe {
  width: 100%; max-width: 1000px; aspect-ratio: 4/3;
  border: 1px solid var(--borda); border-radius: 12px; background: #000;
}
.instrucoes {
  max-width: 1000px; margin: 1rem auto 0; color: var(--suave);
  font-size: .93rem; padding: 0 1.25rem;
}
.instrucoes b { color: var(--texto); }
footer { text-align: center; color: var(--suave); font-size: .85rem;
         padding: 2rem 1rem; }
"""


def pagina(titulo: str, corpo: str, prefixo: str = "") -> str:
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(titulo)}</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#127918;</text></svg>">
<link rel="stylesheet" href="{prefixo}estilo.css">
</head>
<body>
{corpo}
</body>
</html>
"""


def capa_html(jogo: dict, indice: int, prefixo: str) -> str:
    capa = jogo.get("capa")
    if capa and (jogo["pasta"] / capa).exists():
        arquivo = f"{prefixo}capas/{jogo['slug']}{Path(capa).suffix.lower()}"
        return f'<div class="capa"><img src="{esc(arquivo)}" alt="" loading="lazy"></div>'

    a, b = GRADIENTES[indice % len(GRADIENTES)]
    iniciais = "".join(p[0] for p in str(jogo.get("titulo", "?")).split()[:2]).upper()
    return (
        f'<div class="capa" style="background:linear-gradient(135deg,{a},{b})">'
        f"{esc(iniciais)}</div>"
    )


def montar_galeria(jogos: list[dict]) -> str:
    if not jogos:
        corpo_grade = (
            '<p style="text-align:center;color:var(--suave)">'
            "Nenhum jogo publicado ainda.</p>"
        )
    else:
        cartas = []
        for i, jogo in enumerate(jogos):
            cor, rotulo = CORES_ENGINE.get(jogo.get("engine", ""), ("#888", "Jogo"))
            descricao = str(jogo.get("descricao", ""))[:300]
            cartas.append(
                f"""
      <a class="carta" href="j/{esc(jogo['slug'])}.html">
        {capa_html(jogo, i, "")}
        <div class="corpo">
          <span class="etiqueta" style="background:{cor}">{esc(rotulo)}</span>
          <h2>{esc(jogo.get('titulo', 'Sem titulo'))}</h2>
          <div class="autor">{esc(jogo.get('autor', ''))}</div>
          <p class="desc">{esc(descricao)}</p>
          <div class="jogar">Jogar</div>
        </div>
      </a>"""
            )
        corpo_grade = f'<div class="grade">{"".join(cartas)}</div>'

    quantidade = len(jogos)
    plural = "jogo" if quantidade == 1 else "jogos"
    corpo = f"""
<header class="topo">
  <h1>&#127918; {esc(TITULO_SITE)}</h1>
  <p>{esc(SUBTITULO)}</p>
</header>
<div class="envolucro">
  {corpo_grade}
</div>
<footer>
  {quantidade} {plural} publicado(s) &middot; atualizado em
  {date.today().strftime('%d/%m/%Y')}
</footer>
"""
    return pagina(TITULO_SITE, corpo)


def montar_pagina_jogo(jogo: dict) -> str:
    cor, rotulo = CORES_ENGINE.get(jogo.get("engine", ""), ("#888", "Jogo"))
    corpo = f"""
<div class="barra">
  <div>
    <h1>{esc(jogo.get('titulo', ''))}</h1>
    <div class="autor">{esc(jogo.get('autor', ''))}
      &middot; {esc(jogo.get('turma', ''))}</div>
  </div>
  <span class="etiqueta" style="background:{cor}">{esc(rotulo)}</span>
  <a class="voltar" href="../index.html">&larr; todos os jogos</a>
</div>

<div class="palco">
  <iframe src="../jogos/{esc(jogo['slug'])}/index.html"
          title="{esc(jogo.get('titulo', ''))}"
          allow="autoplay; fullscreen; gamepad" allowfullscreen></iframe>
</div>

<div class="instrucoes">
  <p><b>Como jogar:</b> {esc(jogo.get('controles', ''))}</p>
  <p>{esc(jogo.get('descricao', ''))}</p>
  <p style="font-size:.85rem;opacity:.7">Clique dentro do jogo antes de usar
     o teclado.</p>
</div>
<footer><a href="../index.html">Voltar para a galeria</a></footer>
"""
    return pagina(f"{jogo.get('titulo', '')} - {TITULO_SITE}", corpo, prefixo="../")


# ---------------------------------------------------------------- principal


def construir(pular_pygame: bool = False) -> int:
    if SAIDA.exists():
        shutil.rmtree(SAIDA)
    (SAIDA / "j").mkdir(parents=True)
    (SAIDA / "capas").mkdir(parents=True)
    (SAIDA / "estilo.css").write_text(ESTILO, encoding="utf-8")

    jogos = carregar_jogos()
    print(f"{len(jogos)} jogo(s) encontrado(s) em jogos/\n")

    publicados = []
    falhas = 0
    pulados = 0
    for jogo in jogos:
        engine = jogo.get("engine", "")
        print(f"  {jogo['slug']} ({engine})")

        construtor = CONSTRUTORES.get(engine)
        if construtor is None:
            print(f"  ! engine desconhecida: {engine}")
            falhas += 1
            continue
        # Pular por opcao NAO e falha: e o modo rapido usado na validacao de
        # pull request. Contar como erro reprovaria todo PR do repositorio.
        if engine == "pygame" and pular_pygame:
            print("    pulado (--sem-pygame)")
            pulados += 1
            continue

        if not construtor(jogo, SAIDA / "jogos" / jogo["slug"]):
            falhas += 1
            continue

        capa = jogo.get("capa")
        if capa and (jogo["pasta"] / capa).exists():
            destino = SAIDA / "capas" / f"{jogo['slug']}{Path(capa).suffix.lower()}"
            shutil.copy2(jogo["pasta"] / capa, destino)

        (SAIDA / "j" / f"{jogo['slug']}.html").write_text(
            montar_pagina_jogo(jogo), encoding="utf-8"
        )
        publicados.append(jogo)

    (SAIDA / "index.html").write_text(montar_galeria(publicados), encoding="utf-8")
    # o GitHub Pages ignora pastas iniciadas por _ sem este arquivo
    (SAIDA / ".nojekyll").write_text("", encoding="utf-8")

    resumo = f"\nsite/ pronto: {len(publicados)} de {len(jogos)} jogo(s) publicado(s)"
    if pulados:
        resumo += f", {pulados} pulado(s)"
    if falhas:
        resumo += f", {falhas} com falha"
    print(resumo)
    return 1 if falhas else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="monta o site da galeria")
    ap.add_argument("--sem-pygame", action="store_true",
                    help="pula a compilacao WASM (build rapido)")
    ap.add_argument("--servir", action="store_true",
                    help="abre um servidor local depois de construir")
    args = ap.parse_args()

    codigo = construir(pular_pygame=args.sem_pygame)

    if args.servir:
        import http.server
        import socketserver

        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *a, **kw):
                super().__init__(*a, directory=str(SAIDA), **kw)

        with socketserver.TCPServer(("", 8080), Handler) as servidor:
            print("\nservindo em http://localhost:8080  (Ctrl+C para parar)")
            servidor.serve_forever()

    return codigo


if __name__ == "__main__":
    sys.exit(main())
