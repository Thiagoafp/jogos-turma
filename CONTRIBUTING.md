# Como entregar o seu jogo

Sua entrega é um **pull request** neste repositório. Quando ele for aceito, o
jogo aparece no site automaticamente, em poucos minutos.

## O contrato

Você tem um **estúdio** — uma pasta com o seu nome — e dentro dele **uma pasta
por jogo**:

```
atividades/tec-jogos-digitais/cepi-ismael/alunos/
  maria-s/                    ← o seu estúdio
    aluno.json                ← identidade do estúdio (nome, avatar, banner)
    avatar.png
    banner.png
    corrida-espacial/         ← um jogo
      jogo.json
      index.html
    fuga-do-labirinto/        ← outro jogo seu
      jogo.json
      ...
```

Nomes de pasta usam só **letras minúsculas, números e hífen**. Nada de espaço,
acento ou maiúscula.

## A cara do seu estúdio

O `aluno.json` é o que dá identidade à sua página. Copie de
`modelos/aluno.json`. **Tudo aqui é opcional** menos o nome — quem não
configurar nada ganha uma capa colorida com as iniciais.

```json
{
  "nome": "Maria S.",
  "turma": "2026/1",
  "estudio": "NEON PIXEL STUDIO",
  "lema": "Jogos rápidos, difíceis e coloridos.",
  "avatar": "avatar.png",
  "banner": "banner.png",
  "cor": "#7f5af0"
}
```

- **`estudio`** — o nome que aparece grande na sua página. Capriche: é a sua
  marca.
- **`lema`** — uma frase curta (até 160 letras) que diz do que são seus jogos.
- **`avatar`** — a sua "cara": imagem **quadrada**, pelo menos 128×128. É ela
  que aparece no card do estúdio e no topo da sua página.
- **`banner`** — a arte de abertura, **larga**, algo como 1200×320. É o fundo
  do topo da sua página. O nome do estúdio é escrito por cima, então evite
  colocar texto importante na parte de baixo da imagem.
- **`cor`** — sua cor de destaque em `#RRGGBB`, usada quando você não tem
  banner.

Formatos aceitos: `.png`, `.jpg`, `.webp` e `.svg`, até 4 MB cada. Os arquivos
ficam na **sua pasta de estúdio**, não dentro da pasta de um jogo.

Dá para desenhar o avatar no próprio Construct, no Piskel ou em qualquer
editor de pixel art. Veja `alunos/professor/` — o avatar e o banner de
lá são SVG feitos à mão, e você pode abrir para ver como foram montados.

## A ficha de cada jogo

Dentro da pasta de cada jogo vai o **`jogo.json`** e os **arquivos do jogo**,
que mudam conforme a engine.

## O `jogo.json`

Copie de `modelos/` e preencha. Todos os campos são obrigatórios:

```json
{
  "titulo": "Corrida Espacial",
  "autor": "Maria Silva",
  "turma": "2026/1",
  "engine": "construct",
  "descricao": "Desvie dos asteroides e chegue ao fim da fase.",
  "controles": "Setas para mover, espaço para atirar."
}
```

Campos opcionais:

- `"capa": "capa.png"` — imagem do card na galeria (proporção 16×10). Sem
  ela, a galeria gera uma capa colorida com as iniciais.
- `"scratch_id": "123456789"` — só para Scratch, explicado abaixo.
- `"midia": [...]` — a propaganda do jogo, explicada logo abaixo.

## A propaganda do jogo

Cada jogo pode ter **trailer, banners e prints**, que aparecem abaixo do jogo
na página dele:

```json
"midia": [
  { "arquivo": "trailer.mp4", "legenda": "30 segundos de gameplay" },
  { "arquivo": "print-01.png", "legenda": "A fase do vulcão" },
  { "arquivo": "banner.png",  "legenda": "" }
]
```

**O limite é 25 MB de propaganda por jogo**, somando tudo. Esse orçamento é
separado dos arquivos do jogo — um trailer pesado não rouba o espaço de que o
jogo precisa para rodar.

Formatos: `.mp4` e `.webm` para vídeo; `.png`, `.jpg`, `.webp`, `.gif` e
`.svg` para imagem.

Duas dicas que economizam muito espaço:

- Exporte o vídeo em **720p**, não em 1080p. Numa página web ninguém nota a
  diferença, e o arquivo cai pela metade.
- Se usar `.mp4`, confirme que está em **H.264/AAC**. Outros codecs dentro de
  um `.mp4` simplesmente não tocam em alguns navegadores — o aluno vê o vídeo
  funcionando na máquina dele e quebrado no site.

Trinta segundos de 720p bem comprimido cabem folgadamente nos 25 MB.

Salve o arquivo em **UTF-8**. Se o acento aparecer como `Ã§`, está errado.

## O que entregar, por engine

### Construct

No Construct: **Menu → Export → Web (HTML5)**. Ele gera uma pasta com
`index.html` e vários arquivos. Commite **todo o conteúdo** dessa pasta
direto dentro da pasta do jogo, no seu estudio.

Não commite o arquivo `.c3p` do projeto — ele não roda no navegador.

```
alunos/maria-s/corrida-espacial/
  jogo.json
  index.html          ← precisa estar aqui, na raiz
  data.json
  images/ ...
```

### HTML / JavaScript

O arquivo principal precisa se chamar **`index.html`** e ficar na raiz da
sua pasta. Veja `modelos/html/` — é um jogo completo e comentado.

Duas regras que quebram o site publicado:

- Use **caminhos relativos**: `src="imagens/nave.png"`, nunca `src="/imagens/nave.png"`.
- Se usar uma biblioteca, **baixe o arquivo `.js` e commite junto**. Link
  para CDN funciona hoje e quebra quando o CDN sai do ar.

### Python / pygame

Copie `modelos/pygame/` — leia os comentários, eles explicam as três regras.
Resumindo:

1. O arquivo principal se chama **`main.py`**, na raiz da sua pasta.
2. O loop é `async def main()`, iniciado com `asyncio.run(main())`.
3. Todo laço do loop termina com **`await asyncio.sleep(0)`**.

Sem a regra 3 a aba do navegador congela — a página inteira, não só o jogo.

Teste exatamente como vai ficar no site, antes de entregar:

```bash
python -m pygbag main.py
```

Não use `input()`, não escreva arquivos e não use threads: nada disso existe
no navegador.

### Scratch

Duas opções.

**A) Projeto publicado no Scratch** (mais simples). Compartilhe o projeto no
scratch.mit.edu e copie o número do fim do link — em
`scratch.mit.edu/projects/123456789`, o número é `123456789`. Coloque no
`jogo.json`:

```json
{ "engine": "scratch", "scratch_id": "123456789" }
```

Sua pasta terá só o `jogo.json`. O jogo continua morando no Scratch: se você
despublicar, ele some da galeria.

**B) Empacotado com o TurboWarp** (fica independente). Em
[packager.turbowarp.org](https://packager.turbowarp.org), carregue seu `.sb3`,
escolha "HTML único" e baixe. Renomeie o arquivo para **`index.html`** e
commite na sua pasta. Assim o jogo é seu, não depende de mais nada.

## Antes de abrir o pull request

Rode o validador. Ele fala português e aponta o erro exato:

```bash
python ferramentas/validar.py
```

Para ver a galeria como ela vai ficar:

```bash
python ferramentas/construir.py --servir
```

E abra <http://localhost:8080>.

## Abrindo o pull request

1. Faça um **fork** deste repositório (botão "Fork", canto superior direito).
2. Crie a pasta do seu jogo dentro do seu estudio e adicione os arquivos.
3. Commite e envie para o seu fork.
4. Clique em **"Compare & pull request"** e descreva seu jogo em uma frase.

O robô valida o PR em cerca de um minuto. Se aparecer ✗ vermelho, clique em
"Details" para ler o erro, corrija e envie de novo — o PR atualiza sozinho.

Depois que o professor aceitar, o jogo entra no ar automaticamente.

## Limites

- Até **25 MB por arquivo** e **60 MB por pasta**. Comprima imagens e sons.
- Só mexa no **seu** estúdio. PR que altera a pasta de outro aluno é recusado.
- O jogo é público: qualquer pessoa com o link joga, inclusive os pais. Não
  coloque nada que você não mostraria em sala.
