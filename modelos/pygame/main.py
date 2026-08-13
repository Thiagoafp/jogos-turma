"""Modelo de jogo em pygame - copie esta pasta para comecar o seu.

=====================================================================
 AS TRES REGRAS QUE FAZEM O JOGO RODAR NO NAVEGADOR
=====================================================================

O site publica o jogo compilado para WebAssembly (pygbag). Para isso
funcionar, o codigo precisa seguir tres regras. Se voce quebrar
qualquer uma, o jogo trava na tela de carregamento.

  1. O arquivo principal se chama main.py e fica na raiz da sua pasta.

  2. O loop principal e uma funcao `async def main()`, chamada com
     `asyncio.run(main())` na ultima linha do arquivo.

  3. Todo laco do loop principal termina com `await asyncio.sleep(0)`.
     E isso que devolve o controle ao navegador. Sem essa linha a aba
     congela - a pagina inteira, nao so o jogo.

Alem disso:
  - Nao use input(), nao escreva arquivos, nao use threads.
  - Carregue imagens e sons com caminho relativo (ex: "imagens/nave.png")
    e deixe os arquivos dentro da sua pasta.
  - sys.exit() nao existe no navegador: para encerrar, saia do laco.

Rode local:                     python main.py
Rode igual ao site (melhor):    python -m pygbag main.py
=====================================================================
"""

import asyncio
import random

import pygame

LARGURA, ALTURA = 800, 600
FPS = 60

AZUL_FUNDO = (18, 22, 45)
BRANCO = (240, 240, 245)
AMARELO = (255, 210, 60)
VERMELHO = (235, 70, 90)


class Jogador:
    def __init__(self):
        self.rect = pygame.Rect(LARGURA // 2 - 20, ALTURA - 70, 40, 40)
        self.velocidade = 6

    def mover(self, teclas):
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            self.rect.x -= self.velocidade
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            self.rect.x += self.velocidade
        if teclas[pygame.K_UP] or teclas[pygame.K_w]:
            self.rect.y -= self.velocidade
        if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
            self.rect.y += self.velocidade
        self.rect.clamp_ip(pygame.Rect(0, 0, LARGURA, ALTURA))

    def desenhar(self, tela):
        pygame.draw.rect(tela, BRANCO, self.rect, border_radius=8)


class Moeda:
    def __init__(self):
        self.rect = pygame.Rect(0, 0, 22, 22)
        self.reposicionar()

    def reposicionar(self):
        self.rect.x = random.randint(10, LARGURA - 32)
        self.rect.y = random.randint(10, ALTURA - 120)

    def desenhar(self, tela):
        pygame.draw.circle(tela, AMARELO, self.rect.center, 11)


class Inimigo:
    def __init__(self, velocidade):
        self.rect = pygame.Rect(random.randint(0, LARGURA - 30), -30, 30, 30)
        self.velocidade = velocidade

    def atualizar(self):
        self.rect.y += self.velocidade

    def desenhar(self, tela):
        pygame.draw.rect(tela, VERMELHO, self.rect, border_radius=4)


async def main():
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Colete as moedas")
    relogio = pygame.time.Clock()
    fonte = pygame.font.SysFont(None, 34)
    fonte_grande = pygame.font.SysFont(None, 72)

    jogador = Jogador()
    moeda = Moeda()
    inimigos = []
    pontos = 0
    perdeu = False
    quadros = 0

    rodando = True
    while rodando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
            elif evento.type == pygame.KEYDOWN and perdeu and evento.key == pygame.K_r:
                jogador = Jogador()
                moeda = Moeda()
                inimigos = []
                pontos = 0
                quadros = 0
                perdeu = False

        if not perdeu:
            quadros += 1
            jogador.mover(pygame.key.get_pressed())

            if jogador.rect.colliderect(moeda.rect):
                pontos += 1
                moeda.reposicionar()

            # a cada segundo cai um inimigo novo, cada vez mais rapido
            if quadros % FPS == 0:
                inimigos.append(Inimigo(velocidade=3 + pontos * 0.2))

            for inimigo in inimigos:
                inimigo.atualizar()
                if inimigo.rect.colliderect(jogador.rect):
                    perdeu = True
            inimigos = [i for i in inimigos if i.rect.top < ALTURA]

        tela.fill(AZUL_FUNDO)
        moeda.desenhar(tela)
        for inimigo in inimigos:
            inimigo.desenhar(tela)
        jogador.desenhar(tela)
        tela.blit(fonte.render(f"Moedas: {pontos}", True, BRANCO), (16, 16))

        if perdeu:
            aviso = fonte_grande.render("Fim de jogo", True, VERMELHO)
            dica = fonte.render("Aperte R para jogar de novo", True, BRANCO)
            tela.blit(aviso, aviso.get_rect(center=(LARGURA // 2, ALTURA // 2 - 20)))
            tela.blit(dica, dica.get_rect(center=(LARGURA // 2, ALTURA // 2 + 40)))

        pygame.display.flip()
        relogio.tick(FPS)

        # REGRA 3: sem esta linha o navegador congela
        await asyncio.sleep(0)

    pygame.quit()


# REGRA 2: o jogo comeca por aqui
asyncio.run(main())
