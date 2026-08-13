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
PASTA_ATIVIDADES = RAIZ / "atividades"
SAIDA = RAIZ / "site"

TITULO_SITE = "ARCADE DA TURMA"
SUBTITULO = "Jogos criados pelos alunos - escolha um e jogue no navegador"

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


def _ler_json(arquivo: Path) -> dict:
    try:
        return json.loads(arquivo.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
        return {}


def carregar_alunos() -> list[dict]:
    """Percorre atividades/<curso>/<escola>/alunos/<aluno>/<jogo>/.

    A hierarquia existe para escalar: hoje e um curso numa escola, amanha
    entram o TDS e o CEPI Buritis sem mexer em nada. Cada nivel carrega seu
    proprio json com o nome bonito (com acento e maiuscula), enquanto a
    pasta fica em slug - que e o que vai para a URL.

    Um aluno tem VARIOS jogos: a pasta dele e uma prateleira, nao um jogo.
    """
    alunos = []
    if not PASTA_ATIVIDADES.exists():
        return alunos

    for dir_curso in sorted(d for d in PASTA_ATIVIDADES.iterdir() if d.is_dir()):
        curso = _ler_json(dir_curso / "curso.json")
        nome_curso = curso.get("nome", dir_curso.name)

        for dir_escola in sorted(d for d in dir_curso.iterdir() if d.is_dir()):
            escola = _ler_json(dir_escola / "escola.json")
            nome_escola = escola.get("nome", dir_escola.name)

            dir_alunos = dir_escola / "alunos"
            if not dir_alunos.is_dir():
                continue

            for dir_aluno in sorted(d for d in dir_alunos.iterdir() if d.is_dir()):
                ficha = _ler_json(dir_aluno / "aluno.json")
                jogos = []

                for pasta in sorted(d for d in dir_aluno.iterdir() if d.is_dir()):
                    if not (pasta / "jogo.json").exists():
                        continue
                    dados = _ler_json(pasta / "jogo.json")
                    if not dados:
                        print(f"  ! {dir_aluno.name}/{pasta.name}: jogo.json invalido")
                        continue
                    dados["slug"] = pasta.name
                    dados["pasta"] = pasta
                    jogos.append(dados)

                if not jogos:
                    continue

                jogos.sort(key=lambda j: str(j.get("titulo", "")).lower())
                nome = ficha.get("nome", dir_aluno.name)
                alunos.append({
                    "slug": dir_aluno.name,
                    "pasta": dir_aluno,
                    "nome": nome,
                    "turma": ficha.get("turma", escola.get("turma", "")),
                    # identidade do estudio, configurada pelo proprio aluno
                    "estudio": ficha.get("estudio", "") or f"Estudio {nome}",
                    "lema": ficha.get("lema", ""),
                    "cor": ficha.get("cor", ""),
                    "avatar": ficha.get("avatar", ""),
                    "banner": ficha.get("banner", ""),
                    "curso": nome_curso,
                    "curso_slug": dir_curso.name,
                    "escola": nome_escola,
                    "escola_slug": dir_escola.name,
                    "jogos": jogos,
                })

    alunos.sort(key=lambda a: (a["curso_slug"], a["escola_slug"],
                               a["nome"].lower()))
    return alunos


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

    # Apaga build/ INTEIRO, nao so build/web: se a pasta build existir sem a
    # subpasta web, o pygbag nao recria web e falha ao gravar o .apk.
    construido = pasta / "build" / "web"
    if (pasta / "build").exists():
        shutil.rmtree(pasta / "build")

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
  --fundo: #06060f; --carta: #12122a; --borda: #2a2a5c;
  --texto: #eef0ff; --suave: #9aa0cc;
  --neon: #00f0ff; --magenta: #ff2e97; --amarelo: #ffd23c;
}
* { box-sizing: border-box; }

body {
  margin: 0; color: var(--texto); line-height: 1.5;
  font-family: ui-monospace, "Cascadia Mono", Consolas, monospace;
  background:
    radial-gradient(ellipse at 50% -10%, #1a1150 0%, transparent 60%),
    linear-gradient(var(--fundo), #0a0a18);
  background-attachment: fixed;
  min-height: 100vh;
}
/* grade em perspectiva no rodape, tipo cenario de arcade */
body::before {
  content: ""; position: fixed; inset: auto 0 0 0; height: 45vh; z-index: -1;
  background:
    repeating-linear-gradient(90deg, transparent 0 39px, #2a2a5c66 39px 40px),
    repeating-linear-gradient(0deg, transparent 0 39px, #2a2a5c66 39px 40px);
  transform: perspective(320px) rotateX(62deg);
  transform-origin: bottom center;
  mask-image: linear-gradient(transparent, #000 55%);
  pointer-events: none;
}
/* linhas de varredura de monitor CRT */
body::after {
  content: ""; position: fixed; inset: 0; z-index: 999; pointer-events: none;
  background: repeating-linear-gradient(
    0deg, rgba(0,0,0,.16) 0 1px, transparent 1px 3px);
  opacity: .5;
}

a { color: inherit; text-decoration: none; }
.envolucro { max-width: 1220px; margin: 0 auto; padding: 0 1.25rem 5rem; }

header.topo { text-align: center; padding: 3.5rem 1rem 1rem; }
header.topo h1 {
  margin: 0; font-size: clamp(1.7rem, 5.5vw, 3rem);
  letter-spacing: .12em; font-weight: 800; color: #fff;
  text-shadow: 0 0 6px var(--neon), 0 0 22px var(--neon), 0 0 48px #0088ff88;
  animation: piscar 5s infinite;
}
@keyframes piscar {
  0%,96%,100% { opacity: 1 } 97% { opacity: .55 } 98% { opacity: 1 }
}
header.topo p { margin: .9rem 0 0; color: var(--suave); font-size: .9rem; }

/* trilha da hierarquia: Atividades > Curso > Escola > Alunos */
.trilha {
  text-align: center; color: var(--suave); font-size: .72rem;
  letter-spacing: .18em; text-transform: uppercase; padding: 1.5rem 1rem .5rem;
}
.trilha b { color: var(--neon); font-weight: 600; }
.trilha span { opacity: .45; margin: 0 .5rem; }

.secao { margin-top: 2.5rem; }
.secao h2 {
  margin: 0 0 .2rem; font-size: 1rem; letter-spacing: .16em;
  text-transform: uppercase; color: var(--magenta);
  text-shadow: 0 0 12px #ff2e9766;
}
.secao .sub {
  margin: 0 0 1.4rem; color: var(--suave); font-size: .78rem;
  letter-spacing: .14em; text-transform: uppercase;
  border-bottom: 1px solid var(--borda); padding-bottom: .8rem;
}

.grade {
  display: grid; gap: 1.5rem;
  grid-template-columns: repeat(auto-fill, minmax(265px, 1fr));
}

.carta {
  position: relative; background: var(--carta);
  border: 1px solid var(--borda); border-radius: 4px; overflow: hidden;
  display: flex; flex-direction: column;
  transition: transform .18s, box-shadow .18s, border-color .18s;
}
.carta:hover {
  transform: translateY(-6px); border-color: var(--neon);
  box-shadow: 0 0 0 1px var(--neon), 0 0 28px #00f0ff55, 0 16px 40px #000a;
}
.carta .capa {
  aspect-ratio: 16/10; display: grid; place-items: center; position: relative;
  font-size: 2.8rem; font-weight: 800; color: #fff; letter-spacing: .08em;
  text-shadow: 0 3px 18px rgba(0,0,0,.45);
}
.carta .capa::after {
  content: ""; position: absolute; inset: 0;
  background: repeating-linear-gradient(
    0deg, rgba(0,0,0,.22) 0 2px, transparent 2px 4px);
}
.carta .capa img { width: 100%; height: 100%; object-fit: cover; display: block; }
.carta .corpo {
  padding: 1rem 1.1rem 1.2rem; flex: 1;
  display: flex; flex-direction: column; gap: .5rem;
}
.carta h3 { margin: 0; font-size: 1.05rem; color: #fff; letter-spacing: .02em; }
.carta .autor { color: var(--neon); font-size: .8rem; letter-spacing: .08em; }
.carta .desc {
  color: var(--suave); font-size: .82rem; flex: 1; line-height: 1.55;
  font-family: system-ui, sans-serif;
}
.etiqueta {
  align-self: flex-start; font-size: .62rem; font-weight: 700;
  letter-spacing: .12em; text-transform: uppercase;
  padding: .22rem .6rem; border-radius: 2px; color: #06060f;
}
.jogar {
  margin-top: .5rem; text-align: center; font-weight: 700;
  letter-spacing: .18em; font-size: .78rem;
  background: var(--amarelo); color: #14161f;
  padding: .6rem; border-radius: 2px;
}
.carta:hover .jogar { background: var(--neon); }

/* abertura do estudio */
.hero {
  position: relative; min-height: 260px;
  background-size: cover; background-position: center;
  border-bottom: 1px solid var(--borda);
  display: flex; align-items: flex-end;
}
.hero::after {
  content: ""; position: absolute; inset: 0;
  background:
    repeating-linear-gradient(0deg, rgba(0,0,0,.18) 0 2px, transparent 2px 4px),
    linear-gradient(transparent 20%, #06060fdd 92%);
}
.hero-conteudo {
  position: relative; z-index: 1;
  display: flex; align-items: flex-end; gap: 1.4rem; flex-wrap: wrap;
  max-width: 1220px; margin: 0 auto; padding: 2rem 1.25rem 1.6rem; width: 100%;
}
.hero h2 {
  margin: 0; font-size: clamp(1.4rem, 4vw, 2.2rem); color: #fff;
  letter-spacing: .1em; text-shadow: 0 0 10px var(--neon), 0 0 34px #0088ff77;
}
.hero .creditos {
  margin: .5rem 0 0; color: var(--suave); font-size: .78rem;
  letter-spacing: .12em; text-transform: uppercase;
}
.hero .lema {
  margin: .6rem 0 0; color: var(--amarelo); font-size: .95rem;
  font-family: system-ui, sans-serif; font-style: italic; max-width: 60ch;
}

.avatar, .avatar-mini {
  display: grid; place-items: center; overflow: hidden; flex: none;
  font-weight: 800; color: #fff; background: var(--carta);
}
.avatar {
  width: 132px; height: 132px; border-radius: 6px; font-size: 2.6rem;
  border: 2px solid var(--neon);
  box-shadow: 0 0 24px #00f0ff66, 0 10px 30px #000a;
}
.avatar-mini {
  position: absolute; left: 1rem; bottom: 1rem; z-index: 1;
  width: 62px; height: 62px; border-radius: 5px; font-size: 1.2rem;
  border: 2px solid var(--neon); box-shadow: 0 0 16px #00f0ff55;
}
.avatar img, .avatar-mini img {
  width: 100%; height: 100%; object-fit: cover; display: block;
}
.capa-estudio { position: relative; }

/* propaganda do jogo: trailer e prints */
.promo { margin-top: 2.5rem; }
.promo h3 {
  margin: 0 0 1rem; font-size: .8rem; letter-spacing: .18em;
  text-transform: uppercase; color: var(--magenta);
}
.promo figure { margin: 0 0 1rem; }
.promo figcaption {
  margin-top: .4rem; font-size: .8rem; color: var(--suave);
  font-family: system-ui, sans-serif;
}
.promo .trailer video {
  width: 100%; display: block; border-radius: 4px;
  border: 1px solid var(--borda); background: #000;
}
.promo .prints {
  display: grid; gap: .9rem;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
}
.promo .prints img {
  width: 100%; display: block; border-radius: 4px;
  border: 1px solid var(--borda);
}

.vazio {
  text-align: center; color: var(--suave); padding: 4rem 1rem;
  letter-spacing: .1em;
}

/* pagina de um jogo */
.barra {
  display: flex; align-items: center; gap: 1rem; flex-wrap: wrap;
  padding: .9rem 1.25rem; background: #0b0b1e;
  border-bottom: 1px solid var(--borda);
}
.barra h1 {
  margin: 0; font-size: 1.05rem; color: #fff; letter-spacing: .06em;
  text-shadow: 0 0 14px #00f0ff55;
}
.barra .autor { color: var(--suave); font-size: .76rem; letter-spacing: .1em; }
.barra .voltar {
  margin-left: auto; color: var(--suave); font-size: .74rem;
  letter-spacing: .12em; text-transform: uppercase;
}
.barra .voltar:hover { color: var(--neon); }
.palco { padding: 1.5rem 1.25rem; }
.palco iframe {
  /* min() e nao max-width: com grid+max-width o iframe estourava para fora
     da tela em viewport estreita, criando rolagem horizontal na pagina */
  display: block; margin: 0 auto;
  width: min(1000px, 100%); aspect-ratio: 4/3;
  border: 1px solid var(--borda); border-radius: 4px; background: #000;
  box-shadow: 0 0 0 1px #00f0ff33, 0 0 50px #00f0ff22;
}
.instrucoes {
  max-width: 1000px; margin: 1.4rem auto 0; color: var(--suave);
  font-size: .88rem; padding: 0 1.25rem; font-family: system-ui, sans-serif;
}
.instrucoes b { color: var(--amarelo); letter-spacing: .06em; }
footer {
  text-align: center; color: var(--suave); font-size: .72rem;
  letter-spacing: .12em; padding: 3rem 1rem;
}
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


def trilha(*niveis: str) -> str:
    """Atividades > Curso > Escola > Alunos, com o ultimo nivel destacado."""
    partes = []
    for i, nivel in enumerate(niveis):
        if i:
            partes.append("<span>&rsaquo;</span>")
        marca = "b" if i == len(niveis) - 1 else "i"
        partes.append(f"<{marca}>{esc(nivel)}</{marca}>")
    return f'<div class="trilha">{"".join(partes)}</div>'


def iniciais(texto: str) -> str:
    palavras = [p for p in str(texto).split() if len(p) > 2]
    if not palavras:
        return str(texto)[:2].upper()
    return "".join(p[0] for p in palavras[:2]).upper()


def capa_html(jogo: dict, chave: str, indice: int, prefixo: str) -> str:
    capa = jogo.get("capa")
    if capa and (jogo["pasta"] / capa).exists():
        arquivo = f"{prefixo}capas/{chave}{Path(capa).suffix.lower()}"
        return f'<div class="capa"><img src="{esc(arquivo)}" alt="" loading="lazy"></div>'

    a, b = GRADIENTES[indice % len(GRADIENTES)]
    return (
        f'<div class="capa" style="background:linear-gradient(135deg,{a},{b})">'
        f'{esc(iniciais(jogo.get("titulo", "?")))}</div>'
    )


def gradiente_do_aluno(aluno: dict) -> tuple[str, str]:
    """Cor estavel por aluno: nao muda quando outro entra na lista."""
    if aluno.get("cor"):
        return aluno["cor"], aluno["cor"]
    return GRADIENTES[sum(map(ord, aluno["slug"])) % len(GRADIENTES)]


def arquivo_estudio(aluno: dict, campo: str) -> str | None:
    """Caminho publicado do avatar/banner, ou None se o aluno nao mandou."""
    nome = aluno.get(campo)
    if not nome:
        return None
    if not (aluno["pasta"] / nome).exists():
        return None
    chave = f'{aluno["curso_slug"]}--{aluno["escola_slug"]}--{aluno["slug"]}'
    return f"estudios/{chave}-{campo}{Path(nome).suffix.lower()}"


def avatar_html(aluno: dict, prefixo: str, classe: str = "avatar") -> str:
    arquivo = arquivo_estudio(aluno, "avatar")
    if arquivo:
        return (
            f'<div class="{classe}">'
            f'<img src="{esc(prefixo + arquivo)}" alt="" loading="lazy"></div>'
        )
    a, b = gradiente_do_aluno(aluno)
    return (
        f'<div class="{classe}" style="background:linear-gradient(135deg,{a},{b})">'
        f'{esc(iniciais(aluno["nome"]))}</div>'
    )


VIDEOS = {".mp4", ".webm"}


def copiar_midia(aluno: dict, jogo: dict, destino: Path) -> list[dict]:
    """Copia a propaganda do jogo (trailer, banners, prints) para o site."""
    itens = jogo.get("midia")
    if not isinstance(itens, list):
        return []

    publicados = []
    for item in itens:
        if not isinstance(item, dict):
            continue
        nome = str(item.get("arquivo", "")).strip()
        if not nome:
            continue
        origem = jogo["pasta"] / nome
        if not origem.exists():
            print(f"      ! midia ausente: {nome}")
            continue

        destino.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origem, destino / origem.name)
        publicados.append({
            "arquivo": f"midia/{origem.name}",
            "video": origem.suffix.lower() in VIDEOS,
            "legenda": str(item.get("legenda", "")),
        })
    return publicados


def galeria_html(midia: list[dict]) -> str:
    if not midia:
        return ""

    videos = [m for m in midia if m["video"]]
    imagens = [m for m in midia if not m["video"]]
    partes = []

    for m in videos:
        legenda = (
            f'<figcaption>{esc(m["legenda"])}</figcaption>' if m["legenda"] else ""
        )
        partes.append(
            f'<figure class="trailer"><video controls preload="metadata" '
            f'src="{esc(m["arquivo"])}"></video>{legenda}</figure>'
        )

    if imagens:
        tiras = "".join(
            f'<figure><img src="{esc(m["arquivo"])}" alt="{esc(m["legenda"])}" '
            f'loading="lazy">'
            + (f'<figcaption>{esc(m["legenda"])}</figcaption>' if m["legenda"] else "")
            + "</figure>"
            for m in imagens
        )
        partes.append(f'<div class="prints">{tiras}</div>')

    return f"""
<div class="promo">
  <h3>Trailer e imagens</h3>
  {"".join(partes)}
</div>"""


def chave_do_jogo(aluno: dict, jogo: dict) -> str:
    return f'{aluno["curso_slug"]}--{aluno["escola_slug"]}--{aluno["slug"]}--{jogo["slug"]}'


def caminho_do_aluno(aluno: dict) -> str:
    return f'{aluno["curso_slug"]}/{aluno["escola_slug"]}/{aluno["slug"]}'


# ---------------------------------------------------------------- indice


def montar_indice(alunos: list[dict]) -> str:
    """Pagina inicial: a lista de ALUNOS, agrupada por curso e escola."""
    if not alunos:
        corpo_secoes = '<p class="vazio">Nenhum jogo publicado ainda.</p>'
    else:
        secoes = []
        grupo_atual = None
        for aluno in alunos:
            grupo = (aluno["curso"], aluno["escola"])
            if grupo != grupo_atual:
                if grupo_atual is not None:
                    secoes.append("</div></section>")
                secoes.append(
                    f'<section class="secao"><h2>{esc(aluno["curso"])}</h2>'
                    f'<p class="sub">{esc(aluno["escola"])} &middot; Alunos</p>'
                    f'<div class="grade">'
                )
                grupo_atual = grupo

            n = len(aluno["jogos"])
            banner = arquivo_estudio(aluno, "banner")
            a, b = gradiente_do_aluno(aluno)
            fundo = (
                f'background-image:url({esc(banner)});background-size:cover;'
                "background-position:center"
                if banner
                else f"background:linear-gradient(135deg,{a},{b})"
            )
            secoes.append(f"""
      <a class="carta" href="{esc(caminho_do_aluno(aluno))}/">
        <div class="capa capa-estudio" style="{fundo}">
          {avatar_html(aluno, "", "avatar-mini")}
        </div>
        <div class="corpo">
          <h3>{esc(aluno["estudio"])}</h3>
          <div class="autor">{esc(aluno["nome"])} &middot; {esc(aluno["turma"])}</div>
          <p class="desc">{esc(aluno["lema"]) or
             f'{n} {"jogo" if n == 1 else "jogos"} publicado{"" if n == 1 else "s"}.'}</p>
          <div class="jogar">Ver os {n} {"jogo" if n == 1 else "jogos"}</div>
        </div>
      </a>""")
        secoes.append("</div></section>")
        corpo_secoes = "".join(secoes)

    total = sum(len(a["jogos"]) for a in alunos)
    corpo = f"""
<header class="topo">
  <h1>{esc(TITULO_SITE)}</h1>
  <p>{esc(SUBTITULO)}</p>
</header>
{trilha("Atividades")}
<div class="envolucro">
  {corpo_secoes}
</div>
<footer>
  {len(alunos)} aluno(s) &middot; {total} jogo(s) &middot;
  atualizado em {date.today().strftime('%d/%m/%Y')}
</footer>
"""
    return pagina(TITULO_SITE, corpo)


# ---------------------------------------------------------------- loja


def montar_loja(aluno: dict) -> str:
    """A vitrine do aluno: os jogos dele, com cara de loja."""
    cartas = []
    for i, jogo in enumerate(aluno["jogos"]):
        cor, rotulo = CORES_ENGINE.get(jogo.get("engine", ""), ("#888", "Jogo"))
        cartas.append(f"""
      <a class="carta" href="{esc(jogo['slug'])}/">
        {capa_html(jogo, chave_do_jogo(aluno, jogo), i, "../../../")}
        <div class="corpo">
          <span class="etiqueta" style="background:{cor}">{esc(rotulo)}</span>
          <h3>{esc(jogo.get('titulo', 'Sem titulo'))}</h3>
          <div class="autor">{esc(jogo.get('controles', ''))}</div>
          <p class="desc">{esc(str(jogo.get('descricao', ''))[:300])}</p>
          <div class="jogar">Jogar agora</div>
        </div>
      </a>""")

    n = len(aluno["jogos"])
    prefixo = "../../../"

    banner = arquivo_estudio(aluno, "banner")
    a, b = gradiente_do_aluno(aluno)
    fundo_hero = (
        f"background-image:url({esc(prefixo + banner)})"
        if banner
        else f"background-image:linear-gradient(120deg,{a},{b})"
    )
    lema = (
        f'<p class="lema">&ldquo;{esc(aluno["lema"])}&rdquo;</p>'
        if aluno.get("lema")
        else ""
    )

    corpo = f"""
<div class="barra">
  <div>
    <h1>{esc(aluno['estudio'])}</h1>
    <div class="autor">{esc(aluno['nome'])} &middot; {esc(aluno['escola'])}</div>
  </div>
  <a class="voltar" href="{prefixo}index.html">&larr; todos os estudios</a>
</div>

<div class="hero" style="{fundo_hero}">
  <div class="hero-conteudo">
    {avatar_html(aluno, prefixo)}
    <div>
      <h2>{esc(aluno['estudio'])}</h2>
      <p class="creditos">{esc(aluno['nome'])} &middot; {esc(aluno['escola'])}
         &middot; {esc(aluno['turma'])}</p>
      {lema}
    </div>
  </div>
</div>

{trilha("Atividades", aluno["curso"], aluno["escola"], "Alunos", aluno["nome"])}
<div class="envolucro">
  <section class="secao">
    <h2>Jogos do estudio</h2>
    <p class="sub">{n} {"titulo" if n == 1 else "titulos"} publicado{"" if n == 1 else "s"}</p>
    <div class="grade">{"".join(cartas)}</div>
  </section>
</div>
<footer><a href="{prefixo}index.html">Voltar para a lista de estudios</a></footer>
"""
    return pagina(f"{aluno['nome']} - {TITULO_SITE}", corpo, prefixo="../../../")


# ---------------------------------------------------------------- jogar


def montar_pagina_jogo(aluno: dict, jogo: dict, midia: list[dict]) -> str:
    cor, rotulo = CORES_ENGINE.get(jogo.get("engine", ""), ("#888", "Jogo"))
    corpo = f"""
<div class="barra">
  <div>
    <h1>{esc(jogo.get('titulo', ''))}</h1>
    <div class="autor">{esc(aluno['nome'])} &middot; {esc(aluno['escola'])}</div>
  </div>
  <span class="etiqueta" style="background:{cor}">{esc(rotulo)}</span>
  <a class="voltar" href="../index.html">&larr; jogos de {esc(aluno['nome'])}</a>
</div>
{trilha("Atividades", aluno["curso"], aluno["escola"], aluno["nome"],
        str(jogo.get("titulo", "")))}

<div class="palco">
  <iframe src="jogo/index.html" title="{esc(jogo.get('titulo', ''))}"
          scrolling="no" allow="autoplay; fullscreen; gamepad"
          allowfullscreen></iframe>
</div>

<div class="instrucoes">
  <p><b>Como jogar:</b> {esc(jogo.get('controles', ''))}</p>
  <p>{esc(jogo.get('descricao', ''))}</p>
  <p style="font-size:.82rem;opacity:.7">Clique dentro do jogo antes de usar
     o teclado.</p>
  {galeria_html(midia)}
</div>
<footer><a href="../index.html">Voltar</a></footer>
"""
    return pagina(
        f"{jogo.get('titulo', '')} - {aluno['nome']}",
        corpo,
        prefixo="../../../../",
    )


# ---------------------------------------------------------------- principal


def construir(pular_pygame: bool = False) -> int:
    if SAIDA.exists():
        shutil.rmtree(SAIDA)
    (SAIDA / "capas").mkdir(parents=True)
    (SAIDA / "estudios").mkdir(parents=True)
    (SAIDA / "estilo.css").write_text(ESTILO, encoding="utf-8")

    alunos = carregar_alunos()
    total = sum(len(a["jogos"]) for a in alunos)
    print(f"{len(alunos)} aluno(s), {total} jogo(s) em atividades/\n")

    falhas = 0
    pulados = 0
    publicados: list[dict] = []

    for aluno in alunos:
        base = SAIDA / caminho_do_aluno(aluno)
        print(f"  {aluno['nome']} ({aluno['escola']})")

        jogos_ok = []
        for jogo in aluno["jogos"]:
            engine = jogo.get("engine", "")
            print(f"    - {jogo['slug']} ({engine})")

            construtor = CONSTRUTORES.get(engine)
            if construtor is None:
                print(f"      ! engine desconhecida: {engine}")
                falhas += 1
                continue
            # Pular por opcao NAO e falha: e o modo rapido usado na validacao
            # de pull request. Contar como erro reprovaria todo PR.
            if engine == "pygame" and pular_pygame:
                print("      pulado (--sem-pygame)")
                pulados += 1
                continue

            if not construtor(jogo, base / jogo["slug"] / "jogo"):
                falhas += 1
                continue

            capa = jogo.get("capa")
            if capa and (jogo["pasta"] / capa).exists():
                nome = chave_do_jogo(aluno, jogo) + Path(capa).suffix.lower()
                shutil.copy2(jogo["pasta"] / capa, SAIDA / "capas" / nome)

            midia = copiar_midia(aluno, jogo, base / jogo["slug"] / "midia")
            (base / jogo["slug"] / "index.html").write_text(
                montar_pagina_jogo(aluno, jogo, midia), encoding="utf-8"
            )
            jogos_ok.append(jogo)

        if jogos_ok:
            visivel = dict(aluno, jogos=jogos_ok)
            base.mkdir(parents=True, exist_ok=True)

            # avatar e banner do estudio, quando o aluno configurou
            for campo in ("avatar", "banner"):
                destino_rel = arquivo_estudio(aluno, campo)
                if destino_rel:
                    shutil.copy2(
                        aluno["pasta"] / aluno[campo], SAIDA / destino_rel
                    )

            (base / "index.html").write_text(montar_loja(visivel), encoding="utf-8")
            publicados.append(visivel)

    (SAIDA / "index.html").write_text(montar_indice(publicados), encoding="utf-8")
    # o GitHub Pages ignora pastas iniciadas por _ sem este arquivo
    (SAIDA / ".nojekyll").write_text("", encoding="utf-8")

    publicados_n = sum(len(a["jogos"]) for a in publicados)
    resumo = f"\nsite/ pronto: {publicados_n} de {total} jogo(s) publicado(s)"
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
