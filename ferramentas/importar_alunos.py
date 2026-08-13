"""Importa a lista de alunos ativos da plataforma SENAI.

    set DATABASE_URL=postgresql://...
    python ferramentas/importar_alunos.py --escola "CEPI Ismael"

Gera `alunos.json`, que serve para duas coisas:

  - a pagina de upload so aceita envio de quem esta nessa lista;
  - a galeria mostra o nome de exibicao correto.

"Aluno ativo" depende de DUAS colunas diferentes, e confundi-las e o erro
classico aqui:

  sp_alunos.ativo             o cadastro do aluno esta ativo
  sp_alunos_turmas.status     a MATRICULA naquela turma esta ativa

Um aluno transferido continua com sp_alunos.ativo = TRUE, mas com a
matricula encerrada. Filtrar so pelo primeiro traz gente que saiu da turma.

Por privacidade, o site publico mostra "Maria S." e nunca o nome completo:
sao menores de idade numa pagina indexavel. O nome completo fica so no
arquivo interno, para o professor conferir quem entregou.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "alunos.json"

CONSULTA = """
SELECT a.id,
       a.nome,
       t.nome  AS turma,
       e.nome  AS escola
  FROM sp_alunos a
  JOIN sp_alunos_turmas at ON at.aluno_id = a.id
  JOIN sp_turmas  t ON t.id = at.turma_id
  JOIN sp_escolas e ON e.id = t.escola_id
 WHERE a.ativo   = TRUE          -- cadastro ativo
   AND at.status = 'ativo'       -- matricula ativa NESTA turma
   AND t.ativo   = TRUE
   AND e.ativo   = TRUE
   AND e.nome ILIKE $1
   AND ($2::text IS NULL OR t.nome ILIKE $2)
 ORDER BY a.nome
"""


def sem_acento(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def criar_slug(nome: str) -> str:
    base = sem_acento(nome).lower()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    return base


def nome_publico(nome_completo: str) -> str:
    """'Maria Silva Santos' -> 'Maria S.'"""
    partes = [p for p in nome_completo.split() if len(p) > 2 or p.isupper()]
    if not partes:
        return nome_completo
    if len(partes) == 1:
        return partes[0]
    return f"{partes[0]} {partes[1][0].upper()}."


async def importar(escola: str, turma: str | None) -> int:
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("defina DATABASE_URL com a conexao do banco da plataforma")
        return 1

    try:
        import asyncpg
    except ImportError:
        print("falta a dependencia: pip install asyncpg")
        return 1

    conn = await asyncpg.connect(url)
    try:
        linhas = await conn.fetch(CONSULTA, f"%{escola}%", f"%{turma}%" if turma else None)
    finally:
        await conn.close()

    if not linhas:
        print(f"nenhum aluno ativo encontrado para escola ~ '{escola}'"
              + (f" e turma ~ '{turma}'" if turma else ""))
        return 1

    # dois alunos podem virar o mesmo "Maria S."; nesse caso usa duas iniciais
    publicos: dict[str, int] = {}
    for linha in linhas:
        publicos[nome_publico(linha["nome"])] = publicos.get(
            nome_publico(linha["nome"]), 0
        ) + 1

    alunos = []
    vistos: set[str] = set()
    for linha in linhas:
        exibicao = nome_publico(linha["nome"])
        if publicos[exibicao] > 1:
            partes = linha["nome"].split()
            sobrenomes = "".join(p[0].upper() for p in partes[1:3])
            exibicao = f"{partes[0]} {'.'.join(sobrenomes)}."

        # O slug vira pasta E URL publica. Derivar do nome completo
        # publicaria "joao-da-silva" no endereco, anulando a decisao de
        # mostrar so "Joao S." na tela. Deriva do nome de exibicao.
        slug = criar_slug(exibicao)
        sufixo = 2
        while slug in vistos:
            slug = f"{criar_slug(exibicao)}-{sufixo}"
            sufixo += 1
        vistos.add(slug)

        alunos.append({
            "id": linha["id"],
            "slug": slug,
            "nome_completo": linha["nome"],   # interno, nao vai para o site
            "nome_publico": exibicao,
            "turma": linha["turma"],
            "escola": linha["escola"],
        })

    SAIDA.write_text(
        json.dumps({"escola": escola, "alunos": alunos}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"{len(alunos)} aluno(s) ativo(s) gravado(s) em {SAIDA.name}")
    for a in alunos:
        print(f"  {a['nome_publico']:<20} {a['turma']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="importa alunos ativos da plataforma")
    ap.add_argument("--escola", default="Ismael", help="trecho do nome da escola")
    ap.add_argument("--turma", default=None, help="trecho do nome da turma")
    args = ap.parse_args()
    return asyncio.run(importar(args.escola, args.turma))


if __name__ == "__main__":
    sys.exit(main())
