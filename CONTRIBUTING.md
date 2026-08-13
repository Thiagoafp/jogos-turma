# Como entregar o seu jogo

Sua entrega é um **pull request** neste repositório. Quando ele for aceito, o
jogo aparece na galeria automaticamente, em poucos minutos.

## O contrato

Você cria **uma pasta** dentro de `jogos/` com o seu nome e o do jogo:

```
jogos/maria-silva-corrida-espacial/
```

O nome da pasta usa só **letras minúsculas, números e hífen**. Nada de
espaço, acento ou maiúscula.

Dentro dela vão duas coisas: o **`jogo.json`** (a ficha do jogo) e os
**arquivos do jogo**, que mudam conforme a engine.

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

- `"capa": "capa.png"` — imagem do card na galeria (proporção 16×10, até
  25 MB). Sem ela, a galeria gera uma capa colorida com as iniciais.
- `"scratch_id": "123456789"` — só para Scratch, explicado abaixo.

Salve o arquivo em **UTF-8**. Se o acento aparecer como `Ã§`, está errado.

## O que entregar, por engine

### Construct

No Construct: **Menu → Export → Web (HTML5)**. Ele gera uma pasta com
`index.html` e vários arquivos. Commite **todo o conteúdo** dessa pasta
direto dentro da sua pasta em `jogos/`.

Não commite o arquivo `.c3p` do projeto — ele não roda no navegador.

```
jogos/seu-nome-seu-jogo/
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
2. Crie sua pasta em `jogos/` e adicione os arquivos.
3. Commite e envie para o seu fork.
4. Clique em **"Compare & pull request"** e descreva seu jogo em uma frase.

O robô valida o PR em cerca de um minuto. Se aparecer ✗ vermelho, clique em
"Details" para ler o erro, corrija e envie de novo — o PR atualiza sozinho.

Depois que o professor aceitar, o jogo entra no ar automaticamente.

## Limites

- Até **25 MB por arquivo** e **60 MB por pasta**. Comprima imagens e sons.
- Só mexa na **sua** pasta. PR que altera a pasta de outro aluno é recusado.
- O jogo é público: qualquer pessoa com o link joga, inclusive os pais. Não
  coloque nada que você não mostraria em sala.
