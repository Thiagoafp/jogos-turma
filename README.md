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

## Portal de envio dos alunos

O portal permite que cada aluno crie ou edite a identidade do próprio
estúdio e envie jogos em ZIP. A entrega é validada antes de entrar na pasta
do aluno e, quando aprovada, a galeria é reconstruída automaticamente.

Com a galeria aberta na porta 8080, rode em outro terminal:

```bash
python ferramentas/portal.py
```

Abra <http://localhost:8081>. Na primeira execução, o terminal mostra um
código individual para cada aluno. Esses códigos ficam somente em
`.portal/acessos.json`, que é ignorado pelo Git. A lista pronta para o
professor fica em `.portal/codigos-iniciais.txt`. Para invalidar os códigos
anteriores e gerar uma lista nova:

```bash
python ferramentas/portal.py --redefinir-codigos
```

Para os alunos acessarem pela mesma rede local, descubra o IP do computador
do professor e inicie com `--host 0.0.0.0`; eles então abrem
`http://IP-DO-PROFESSOR:8081`. Essa modalidade é apropriada à rede da sala.
Para publicar o portal na internet será necessário usar um serviço com
autenticação e armazenamento persistente; o site estático do Render não
consegue receber arquivos.

No Windows, basta dar dois cliques em `iniciar-portal-alunos.cmd`. O iniciador
mostra na tela os endereços que podem ser passados aos alunos e mantém o
portal aberto para a rede da sala.

## Publicação

Dois workflows, em `.github/workflows/`:

- **`validar.yml`** — roda em cada pull request. Confere estrutura,
  metadados e as regras de cada engine, e monta o site sem compilar WASM. O
  aluno vê o erro em português, no próprio PR, antes de qualquer merge.
- **`publicar.yml`** — roda a cada push na `main`. Compila tudo e empurra o
  resultado para a branch **`publicado`**, que é o que o **Render** serve.

### Por que o Render não constrói o site

O build precisa de Python e do pygbag, que baixa um runtime WebAssembly de
dezenas de MB. O ambiente de build de site estático do Render não garante
nenhum dos dois — e uma falha lá derrubaria o site inteiro, inclusive os jogos
de Construct e HTML que não têm nada a ver com Python.

Então a divisão é: **o GitHub Actions constrói, o Render serve**. O Render só
precisa saber entregar arquivo, que é o que ele faz bem.

A branch `publicado` é descartável: contém só o site montado, com histórico
achatado. Nunca edite nada nela — o próximo deploy sobrescreve tudo.

### Configurando o Render (uma vez só)

1. No painel do Render: **New → Static Site**, conectando este repositório.
2. Em **Branch**, escolha `publicado` (não `main`).
3. **Build Command**: deixe vazio.
4. **Publish Directory**: `.`
5. Crie. A partir daí, todo merge na `main` atualiza o site sozinho.

O `render.yaml` na raiz já traz essa configuração como Blueprint — ajuste a
linha `repo:` para o endereço real depois de criar o repositório no GitHub.

**Site estático no Render não hiberna.** Quem dorme no plano gratuito é o Web
Service. Um pai abrindo o link às 22h de domingo vai encontrar o site no ar —
foi justamente por isso que a galeria é estática.

## Por que não tem banco de dados

A galeria é um site estático: HTML, CSS e os arquivos dos jogos. Não há
Supabase nem serviço no Render porque não há nada para guardar — a lista de
jogos *é* o conteúdo do repositório, e o histórico de entregas *é* o
histórico do git.

Isso não é economia à toa: um site estático não cai, não hiberna, não expira
credencial e não tem custo. Se fosse um Web Service no Render, o plano
gratuito dormiria depois de 15 minutos sem acesso — e a primeira visita do dia
levaria quase um minuto para responder. Um pai abrindo o link daqui a dois anos vai
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
