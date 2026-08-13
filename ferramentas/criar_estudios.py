"""Cria a pasta de estudio de cada aluno ativo, a partir do alunos.json.

    python ferramentas/importar_alunos.py --escola "Ismael"
    python ferramentas/criar_estudios.py --curso tec-jogos-digitais \\
                                         --escola cepi-ismael

Nunca sobrescreve: se o aluno ja configurou o estudio dele (nome, avatar,
banner), rodar de novo nao apaga nada. So cria o que falta - o que permite
rodar isto toda vez que entrar aluno novo na turma.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
LISTA = RAIZ / "alunos.json"


def main() -> int:
    ap = argparse.ArgumentParser(description="cria os estudios dos alunos ativos")
    ap.add_argument("--curso", required=True, help="slug da pasta do curso")
    ap.add_argument("--escola", required=True, help="slug da pasta da escola")
    args = ap.parse_args()

    if not LISTA.exists():
        print("rode antes: python ferramentas/importar_alunos.py")
        return 1

    dados = json.loads(LISTA.read_text(encoding="utf-8"))
    alunos = dados.get("alunos", [])
    if not alunos:
        print("alunos.json esta vazio")
        return 1

    destino = RAIZ / "atividades" / args.curso / args.escola / "alunos"
    if not destino.parent.exists():
        print(f"pasta nao existe: {destino.parent}")
        print("crie o curso e a escola antes (curso.json / escola.json)")
        return 1
    destino.mkdir(parents=True, exist_ok=True)

    criados = mantidos = 0
    for aluno in alunos:
        pasta = destino / aluno["slug"]
        ficha = pasta / "aluno.json"

        if ficha.exists():
            mantidos += 1
            continue

        pasta.mkdir(parents=True, exist_ok=True)
        ficha.write_text(
            json.dumps(
                {
                    "nome": aluno["nome_publico"],
                    "turma": "",   # herda a turma da escola; o aluno pode sobrescrever
                    "estudio": "",   # o aluno escolhe; vazio usa "Estudio <nome>"
                    "lema": "",
                    "avatar": "",
                    "banner": "",
                    "cor": "",
                },
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        criados += 1
        print(f"  criado  {aluno['slug']:<16} {aluno['nome_publico']}")

    print(f"\n{criados} estudio(s) criado(s), {mantidos} ja existiam (nao tocados)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
