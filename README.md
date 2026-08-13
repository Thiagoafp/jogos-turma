# 🎮 Jogos da Turma

Galeria pública dos jogos criados pelos alunos. Cada entrega vira uma página
que roda no navegador — os pais abrem o link no celular e jogam, sem instalar
nada, sem login.

**Aluno entregando um jogo?** Leia o [CONTRIBUTING.md](CONTRIBUTING.md).

---

## A ideia central

Os alunos usam engines diferentes — Construct, Scratch, HTML, pygame. Fazer
um pipeline para cada uma seria insustentável. Em vez disso, existe **um
contrato único**:

> todo jogo, venha de onde vier, vira uma pasta com um `index.html`.

A galeria não sabe o que é Construct ou pygame. Ela só embute páginas. O que
muda por engine é apenas *como se chega* a esse `index.html`:

| Engine | Aluno entrega | O que o build faz |
|---|---|---|
| **Construct** | a pasta exportada (Export → Web) | copia |
| **HTML/JS** | `index.html` + assets | copia |
| **pygame** | `main.py` | compila para WebAssembly com pygbag |
| **Scratch** | o número do projeto publicado | gera a página com o player oficial |

Adicionar uma engine nova no futuro é escrever uma função em
`ferramentas/construir.py` e registrá-la no dicionário `CONSTRUTORES`.

## Estrutura

```
jogos/                    uma pasta por entrega (é aqui que o aluno mexe)
  fulano-nome-do-jogo/
    jogo.json             ficha: título, autor, turma, engine, controles
    ...                   os arquivos do jogo

modelos/                  ponto de partida para copiar
  pygame/                 jogo completo e comentado, já no formato async
  html/                   jogo completo em canvas 2D

ferramentas/
  validar.py              confere as entregas (roda em cada PR)
  construir.py            monta o site/ a partir de jogos/

site/                     gerado pelo build — não commite, não edite à mão
```

## Rodando

```bash
pip install pygbag pygame
```

```bash
python ferramentas/construir.py --servir
```

Abra <http://localhost:8080>. Para um build rápido, sem compilar os jogos
pygame (que é a parte lenta):

```bash
python ferramentas/construir.py --sem-pygame
```

## Publicação

Dois workflows, em `.github/workflows/`:

- **`validar.yml`** — roda em cada pull request. Confere estrutura,
  metadados e as regras de cada engine, e monta o site sem compilar WASM. O
  aluno vê o erro em português, no próprio PR, antes de qualquer merge.
- **`publicar.yml`** — roda a cada push na `main`. Compila tudo e publica no
  **Cloudflare Pages**.

### Configurando o Cloudflare (uma vez só)

1. No painel da Cloudflare: **Workers & Pages → Create → Pages → Direct
   Upload**, com o nome `jogos-turma`.
2. Crie um **API token** com a permissão `Cloudflare Pages: Edit`.
3. No GitHub, em **Settings → Secrets and variables → Actions**, adicione:
   - `CLOUDFLARE_API_TOKEN`
   - `CLOUDFLARE_ACCOUNT_ID`

Esse token é do Pages e **não tem relação com o token de R2** usado em outros
projetos — são produtos e credenciais separados.

## Por que não tem banco de dados

A galeria é um site estático: HTML, CSS e os arquivos dos jogos. Não há
Supabase nem serviço no Render porque não há nada para guardar — a lista de
jogos *é* o conteúdo do repositório, e o histórico de entregas *é* o
histórico do git.

Isso não é economia à toa: um site estático não cai, não hiberna, não expira
credencial e não tem custo. Um pai abrindo o link daqui a dois anos vai
encontrar o jogo do filho no ar.

Banco só passaria a fazer sentido com estado de verdade: placar entre
visitantes, comentários, contador de acessos. Aí o Supabase entra bem — e o
site continua estático, chamando a API do navegador.

## Detalhes que importam

**Os jogos pygame dependem de um CDN externo.** O pygbag gera uma página
leve (~50 KB) que baixa o interpretador Python em WebAssembly de
`pygame-web.github.io`. Se esse domínio sair do ar, os jogos pygame param —
os de Construct, HTML e Scratch-empacotado não. Dá para hospedar o runtime
junto, mas são dezenas de MB por jogo.

**Scratch por `scratch_id` mora no Scratch.** A galeria embute o player
oficial. Se o aluno despublicar o projeto, o card fica lá e o jogo não
carrega. Para entrega definitiva, prefira o TurboWarp Packager.

**O primeiro carregamento de um jogo pygame é lento** (o runtime tem alguns
MB). Depois fica em cache. Vale avisar os pais na apresentação.

**`site/` é gerado.** Está no `.gitignore`. Nunca edite à mão: o próximo
build apaga tudo.
